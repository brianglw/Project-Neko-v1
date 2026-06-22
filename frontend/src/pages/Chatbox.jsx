import { ChatBox } from '@mui/x-chat';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import { useState } from 'react';
import {useChatContext} from '../contexts/ChatContext.jsx'
import shoyuAvatarUrl from '../assets/shoyu_neutral2.jpg'

const Chatbox = () => {
    const {history, handleChat, setHistory} = useChatContext()
    const [isWaitingForReply, setIsWaitingForReply] = useState(false)

    const handleMessagesChange = (messages) => {
        setHistory(messages)
    }

    const adapter = {
        async sendMessage({ message }) {
            console.log("Chatbox message", message)
            console.log("Chatbox history in sendMessage at start of call", history)

            setIsWaitingForReply(true)
            const msgs = await handleChat(message).finally(() => {
                setIsWaitingForReply(false)
            })
            const replyMessage = msgs?.memo?.at(-1)
            const reply = replyMessage?.parts?.find((part) => part.type === 'text')?.text

            if (!replyMessage?.id || reply == null) {
                throw new Error('Chat generation failed')
            }

            const messageId = replyMessage.id
            const textId = `${messageId}-text`

            return new ReadableStream({
                start(controller) {
                    controller.enqueue({ type: 'start', messageId });
                    controller.enqueue({ type: 'text-start', id: textId });
                    controller.enqueue({ type: 'text-delta', id: textId, delta: reply });
                    controller.enqueue({ type: 'text-end', id: textId });
                    controller.enqueue({ type: 'finish', messageId });
                    controller.close()
                }
            })
        }
    }
    return (
        <Box sx={{ position: 'relative' }}>
            <ChatBox
                adapter={adapter}
                messages={history}
                onMessagesChange={handleMessagesChange}
                sx={{ height: 750 }}
            />
            {isWaitingForReply ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    <Avatar src={shoyuAvatarUrl} alt="Shoyu" sx={{ width: 32, height: 32 }} />
                    <Chip label="..." color="info" size="small" />
                </Box>
            ) : null}
        </Box>
    );
}

export default Chatbox
