import { ChatBox } from '@mui/x-chat';
import {useChatContext} from '../contexts/ChatContext.jsx'

const Practice = () => {
    const {history, handleChat, setHistory} = useChatContext()

    const handleMessagesChange = (messages) => {
        const lastMessage = messages?.at(-1)
        // #region agent log
        fetch('http://127.0.0.1:7370/ingest/e731b92c-5972-4901-90c1-5422fcbe8775',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'9db512'},body:JSON.stringify({sessionId:'9db512',runId:'initial',hypothesisId:'H6,H7',location:'frontend/src/pages/Practice.jsx:8',message:'mui messages changed',data:{messageCount:messages?.length ?? 0,lastKeys:lastMessage ? Object.keys(lastMessage) : [],lastRole:lastMessage?.role,lastStatus:lastMessage?.status,lastPartTypes:lastMessage?.parts?.map((part)=>part.type),hasAuthor:Boolean(lastMessage?.author),hasCreatedAt:Boolean(lastMessage?.createdAt),hasConversationId:Boolean(lastMessage?.conversationId)},timestamp:Date.now()})}).catch(()=>{});
        // #endregion
        setHistory(messages)
    }

    const adapter = {
        async sendMessage({ message }) {
            console.log("Practice message", message)
            console.log("Practice history in sendMessage at start of call", history)

            const msgs = await handleChat(message)
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
        <ChatBox
            adapter={adapter}
            messages={history}
            onMessagesChange={handleMessagesChange}
            sx={{ height: 500 }}
        />
    );
}

export default Practice