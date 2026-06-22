import { useState } from 'react'
import {Routes, Route, Link} from 'react-router-dom'

import { ChatProvider } from './contexts/ChatContext.jsx'
import Home from './pages/Home.jsx'
import Chatbox from './pages/Chatbox.jsx'
import './App.css'

function App() {

  return (
    <>
      <ChatProvider>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
        <Routes>
          <Route path="/chatbox" element={<Chatbox />} />
        </Routes>
      </ChatProvider>
    </>
  )
}

export default App
