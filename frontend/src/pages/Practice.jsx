import {useState} from 'react'
import { ChatBox } from '@mui/x-chat';
import api from '../services/api.js'
import {useChatContext} from '../contexts/ChatContext.jsx'



const Practice = () => {
    const {history, handleSubmit, handleTextChange, handleKeyEvent, msg, setMsg, handleClearChat, setHistory, setChatLog} = useChatContext()


    const adapter = {
        // const res = await fetch('/api/chat', {
        //     method: 'POST',
        //     body: JSON.stringify({ message }),
        //     signal,
        // });
        // return res.body; // ReadableStream<ChatMessageChunk>
        async sendMessage({ message, signal }) {
            let resp
            console.log("sendMessage adapter message", message)
            console.log("sendMessage adapter signal", signal)
            const formatted_msg = {'role': message['role'], 'content': message['parts'][0]['text']}
            console.log("formatted msg before api /chat", formatted_msg)

            await api.post("/chat", {'memo': [...history, formatted_msg]})
            .then((response) => {
               resp = response.data['memo']
                console.log(`Home.jsx`, response.data)
                if (resp.length > 0) {
                    setHistory((prev) => (resp))
                    console.log("sendMessage /chat history", resp)
                    setChatLog((prev) => ([...prev, resp.at(-1)]))
                    // handleDumpDB(response.data['memo'].slice(-2), "history")
                    // handleDumpDB(response.data['memo'].slice(-2), "chatlog")
                    // console.log("Home.jsx handleChat(): Files saved")
                } 
            })
            .catch((error) => {
                console.error(`Home.jsx ${handleChat.name}`, error);
            })

            console.log("sendMessage returning data")
            return new ReadableStream({
                start(controller) {
                    controller.enqueue({ type: 'start', messageId: 'msg-1' });
                    controller.enqueue({ type: 'text-start', id: 'text-1' });
                    controller.enqueue({ type: 'text-delta', id: 'text-1', delta: resp?.at(-1)['content'] });
                    controller.enqueue({ type: 'text-end', id: 'text-1' });
                    controller.enqueue({ type: 'finish', messageId: 'msg-1' });
                    controller.close()
                }
            })
        }
    }
    return (
        <ChatBox
            adapter={adapter}
            initialMessages={history}
            sx={{ height: 500 }}
        />
    );
}

export default Practice