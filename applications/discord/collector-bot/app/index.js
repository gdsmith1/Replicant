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

async function recordAudio(connection) {
    console.log('Recording started.');
    const receiver = connection.receiver;

    const audioDir = path.join(__dirname, 'audio');
    if (!fs.existsSync(audioDir)) {
        fs.mkdirSync(audioDir);
    }

    const audioStream = receiver.subscribe(USER_ID, {
        end: {
            behavior: EndBehaviorType.Manual,
        },
    });

    const outputPath = path.join(audioDir, `${USER_ID}-${Date.now()}.wav`);
    const fileWriter = new wav.FileWriter(outputPath, {
        sampleRate: 48000,
        channels: 2,
    });

    const pcmStream = new prism.opus.Decoder({ rate: 48000, channels: 2, frameSize: 960 });
    audioStream.pipe(pcmStream).pipe(fileWriter);

    fileWriter.on('finish', async () => {
        console.log('Recording finished.');
        await uploadToS3(outputPath);
        connection.destroy();
        client.destroy();
    });

    setTimeout(() => {
        console.log('Stopping recording.');
        fileWriter.end();
    }, 60000); // Adjust the duration as needed
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
        console.log(`File uploaded successfully to ${S3_BUCKET_NAME}/${path.basename(filePath)}`);
    } catch (error) {
        console.error('Error uploading file:', error);
    }
}

client.login(TOKEN);