require("dotenv").config();
const { Client, GatewayIntentBits, ChannelType } = require("discord.js");
const {
  joinVoiceChannel,
  VoiceConnectionStatus,
  EndBehaviorType,
} = require("@discordjs/voice");
const prism = require("prism-media");
const fs = require("fs");
const path = require("path");
const wav = require("wav");
const { S3Client, PutObjectCommand } = require("@aws-sdk/client-s3");

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildMembers,
  ],
});

const TOKEN = process.env.DISCORD_BOT_TOKEN;
const CHANNEL_ID = process.env.VOICE_CHANNEL_ID;
const USER_ID = process.env.TARGET_USER_ID;
const timeLimit = (process.env.TIME_LIMIT || 600) * 1000; // 10 minutes in seconds
const speakingLimit = (process.env.SPEAKING_LIMIT || 5) * 1000; // 5 seconds in seconds

// Function to get the dynamic bucket name
function getBucketName() {
  const awsAccessKey = process.env.AWS_ACCESS_KEY_ID || "";
  // Take first 8 characters and convert to lowercase
  const keyPrefix = awsAccessKey.substring(0, 8).toLowerCase();
  const bucketName = `replicant-s3-${keyPrefix}`;
  console.log(`Using S3 bucket name: ${bucketName}`);
  return bucketName;
}

const S3_BUCKET_NAME = getBucketName();

// Load AWS credentials from environment variables
const s3Client = new S3Client({
  region: "us-east-1",
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  },
});

let deletedFilesCount = 0;
let successfulFilesCount = 0;

client.once("ready", async () => {
  console.log(`Logged in as ${client.user.tag}!`);

  const channel = await client.channels.fetch(CHANNEL_ID);
  if (!channel || channel.type !== ChannelType.GuildVoice) {
    console.error("The channel is not a voice channel or does not exist.");
    return;
  }

  const connection = joinVoiceChannel({
    channelId: channel.id,
    guildId: channel.guild.id,
    adapterCreator: channel.guild.voiceAdapterCreator,
    selfDeaf: false, // Ensure the bot is not deafened
  });

  connection.on(VoiceConnectionStatus.Ready, () => {
    console.log("The bot has connected to the channel!");
    recordAudio(connection);
  });
});

async function recordAudio(connection) {
  console.log("Recording started.");
  const receiver = connection.receiver;

  const audioDir = path.join(__dirname, "audio");
  if (!fs.existsSync(audioDir)) {
    fs.mkdirSync(audioDir);
  }

  const stopRecording = setTimeout(() => {
    console.log("Time limit reached!");
    connection.disconnect();
    client.destroy();
    console.log(`Total deleted files: ${deletedFilesCount}`);
    console.log(`Total successful files: ${successfulFilesCount}`);
  }, timeLimit); // Stop recording anything after this time

  let isRecording = false;
  let recordingTimeout; // Add this line to store the timeout ID

  // This event is triggered when a user starts speaking, and should only do anything if the user is the target user and not already recording.
  receiver.speaking.on("start", (userId) => {
    // Record speaking events
    console.log(`User ${userId} started speaking.`);
    if (!isRecording && userId === USER_ID) {
      console.log("Listening...");
      isRecording = true;
      const startTime = Date.now();
      const outputPath = path.join(audioDir, `${USER_ID}-${startTime}.wav`);
      const fileWriter = new wav.FileWriter(outputPath, {
        sampleRate: 48000,
        channels: 2,
      });

      const audioStream = receiver.subscribe(USER_ID, {
        end: {
          behavior: EndBehaviorType.Manual,
        },
      });

      const pcmStream = new prism.opus.Decoder({
        rate: 48000,
        channels: 2,
        frameSize: 960,
      });
      audioStream.pipe(pcmStream).pipe(fileWriter);

      // Clear any existing timeout before setting a new one
      if (recordingTimeout) {
        clearTimeout(recordingTimeout);
      }

      // Stop recording sentence after a certain time
      recordingTimeout = setTimeout(() => {
        console.log("Stopping recording for this speaking event.");
        fileWriter.end();
        audioStream.destroy();
        pcmStream.destroy();
        isRecording = false;
      }, speakingLimit); // Time for each speaking event

      // When the speaking event ends, stop recording and upload the file to S3
      fileWriter.on("finish", async () => {
        const fileSize = fs.statSync(outputPath).size / 1024; // File size in KB
        console.log(`File size: ${fileSize.toFixed(2)} KB.`);
        if (fileSize > 4) {
          // Minimum file size for a valid recording
          console.log("Recording finished.");
          await uploadToS3(outputPath);
          successfulFilesCount++;
        } else {
          console.log("Recording too short, deleting file.");
          fs.unlinkSync(outputPath);
          deletedFilesCount++;
        }
        isRecording = false; // Reset the flag here
      });

      // Log any errors that occur during the recording process
      fileWriter.on("error", (error) => {
        console.error("Error during recording:", error);
        isRecording = false;
      });

      audioStream.on("error", (error) => {
        console.error("Error with audio stream:", error);
        isRecording = false;
      });

      pcmStream.on("error", (error) => {
        console.error("Error with PCM stream:", error);
        isRecording = false;
      });
    } else {
      console.log("Already recording, ignoring this speaking event.");
    }
  });

  async function uploadToS3(filePath) {
    const fileContent = fs.readFileSync(filePath);
    const params = {
      Bucket: S3_BUCKET_NAME,
      Key: path.basename(filePath),
      Body: fileContent,
    };

    try {
      const command = new PutObjectCommand(params);
      await s3Client.send(command);
      console.log(
        `File uploaded successfully to ${S3_BUCKET_NAME}/${path.basename(filePath)}`,
      );
    } catch (error) {
      console.error("Error uploading file:", error);
    }
  }
}

client.login(TOKEN);
