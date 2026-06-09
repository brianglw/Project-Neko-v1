import {
  ChatConversation,
  ChatConversationHeader,
  ChatConversationTitle,
  ChatConversationSubtitle,
  ChatConversationHeaderActions,
  ChatMessageList,
  ChatMessageGroup,
  ChatComposer,
  ChatComposerTextArea,
  ChatComposerToolbar,
  ChatComposerSendButton,
} from '@mui/x-chat';
import Box from '@mui/material/Box';

import {useChatContext} from '../contexts/ChatContext.jsx'

const ChatMessages = () => {
    try {
        const {history, isLoading} = useChatContext()
        console.log("ChatMessages.jsx", history)

        const ChatMessage = ({role,content}) => {
            return (
                <p>{`${role}: ${content}`}</p>
            )
        }

        const LoadingMessage = () => {
            <p>...</p>
        }

        return (
            <div>
                {(history ?? [])?.map((msg, index) => {
                    return <ChatMessage key={index} role={msg.role} content={msg.content}></ChatMessage>
                })
                }
                {isLoading ? <LoadingMessage /> : ""}
            </div>
        )
    } catch (e) {
        console.log("ChatMessages.jsx error:", e)
    }
}

export default ChatMessages