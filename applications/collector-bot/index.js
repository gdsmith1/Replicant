require('dotenv').config();
const { Client, GatewayIntentBits, ChannelType } = require('discord.js');
const { joinVoiceChannel, VoiceConnectionStatus, EndBehaviorType } = require('@discordjs/voice');
const prism = require('prism-media');
const fs = require('fs');
const path = require('path');
const wav = require('wav');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');

const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates, GatewayIntentBits.GuildMembers] });

const TOKEN = process.env.DISCORD_BOT_TOKEN;
const CHANNEL_ID = process.env.VOICE_CHANNEL_ID;
const USER_ID = process.env.TARGET_USER_ID;
const S3_BUCKET_NAME = "replicant-s3-bucket"; // Set in terraform
const timeLimit = process.env.TIME_LIMIT || 600000; // 10 minutes
const speakingLimit = process.env.SPEAKING_LIMIT || 5000; // 5 seconds

// Load AWS credentials from environment variables
const s3Client = new S3Client({ 
    region: "us-east-1",
    credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
    }
});
client.once('ready', async () => {
    console.log(`Logged in as ${client.user.tag}!`);

    const channel = await client.channels.fetch(CHANNEL_ID);
    if (!channel || channel.type !== ChannelType.GuildVoice) {
        console.error('The channel is not a voice channel or does not exist.');
        return;
    }

    const connection = joinVoiceChannel({
        channelId: channel.id,
        guildId: channel.guild.id,
        adapterCreator: channel.guild.voiceAdapterCreator,
        selfDeaf: false, // Ensure the bot is not deafened
    });

    connection.on(VoiceConnectionStatus.Ready, () => {
        console.log('The bot has connected to the channel!');
        recordAudio(connection);
    });
});

let isRecording = false;

async function recordAudio(connection) {
    console.log('Recording started.');
    const receiver = connection.receiver;

    const audioDir = path.join(__dirname, 'audio');
    if (!fs.existsSync(audioDir)) {
        fs.mkdirSync(audioDir);
    }

    const stopRecording = setTimeout(() => {
        console.log('Stopping recording after 2 minutes.');
        connection.disconnect();
        client.destroy();
    }, timeLimit); // Stop recording anything after this time

    receiver.speaking.on('start', userId => { // Record speaking events
        if (userId === USER_ID && !isRecording) { // Only record the target user and if not already recording
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

            const pcmStream = new prism.opus.Decoder({ rate: 48000, channels: 2, frameSize: 960 });
            audioStream.pipe(pcmStream).pipe(fileWriter);

            fileWriter.on('finish', async () => {
                const duration = (Date.now() - startTime) / 1000;
                if (duration > 0.25) { // Arbitrary minimum duration for a valid recording
                    console.log('Recording finished.');
                    await uploadToS3(outputPath);
                } else {
                    console.log('Recording too short, deleting file.');
                    fs.unlinkSync(outputPath);
                }
            });

            setTimeout(() => {
                console.log('Stopping recording for this speaking event.');
                fileWriter.end();
                isRecording = false;
            }, speakingLimit); // Time for each speaking event
        }
    });
}

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
        console.log(`File uploaded successfully to ${S3_BUCKET_NAME}/audio/${path.basename(filePath)}`);
    } catch (error) {
        console.error('Error uploading file:', error);
    }
}

client.login(TOKEN);
 