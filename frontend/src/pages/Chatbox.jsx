import { ChatBox } from '@mui/x-chat';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import { useState } from 'react';
import {useChatContext} from '../contexts/ChatContext.jsx'
import shoyuAvatarUrl from '../assets/shoyu_neutral2.jpg'

const Chatbox = () => {
    const {history, streamChat, setHistory} = useChatContext()
    const [isWaitingForReply, setIsWaitingForReply] = useState(false)

    const handleMessagesChange = (messages) => {
        setHistory(messages)
    }

    const adapter = {
        async sendMessage({ message }) {
            console.log("Chatbox message", message)
            console.log("Chatbox history in sendMessage at start of call", history)

            setIsWaitingForReply(true)
            let chunkStream
            try {
                chunkStream = await streamChat(message)
            } catch (error) {
                setIsWaitingForReply(false)
                throw error
            }

            const clearBadge = new TransformStream({
                transform(chunk, controller) {
                    if (chunk?.type === 'text-delta') {
                        setIsWaitingForReply(false)
                    }
                    controller.enqueue(chunk)
                },
                flush() {
                    setIsWaitingForReply(false)
                },
            })

            return chunkStream.pipeThrough(clearBadge)
        }
    }
    return (
        <Box sx={{ position: 'relative' }}>
            {isWaitingForReply ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    <Avatar src={shoyuAvatarUrl} alt="Shoyu" sx={{ width: 32, height: 32 }} />
                    <Chip label="..." color="info" size="small" />
                </Box>
            ) : null}
            <ChatBox
                adapter={adapter}
                messages={history}
                onMessagesChange={handleMessagesChange}
                sx={{ height: 750 }}
            />
        </Box>
    );
}

export default Chatbox
