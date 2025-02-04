const { Client, GatewayIntentBits, ChannelType } = require('discord.js');
const { joinVoiceChannel, VoiceConnectionStatus, EndBehaviorType } = require('@discordjs/voice');
const prism = require('prism-media');
const fs = require('fs');
const path = require('path');
const wav = require('wav');

const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates, GatewayIntentBits.GuildMembers] });

const TOKEN = 'YOUR_BOT_TOKEN';
const CHANNEL_ID = 'YOUR_VOICE_CHANNEL'; // Voice channel ID to join
const USER_ID = 'YOUR_TARGET_USER'; // User ID of the member to record

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

    setTimeout(() => {
        console.log('Stopping recording.');
        fileWriter.end();
        connection.destroy();
        client.destroy();
    }, 300000); // Adjust the duration as needed
}

client.login(TOKEN);