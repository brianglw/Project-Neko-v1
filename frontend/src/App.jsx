import { useState } from 'react'
import {Routes, Route, Link} from 'react-router-dom'

import { ChatProvider } from './contexts/ChatContext.jsx'
import Home from './pages/Home.jsx'
import Practice from './pages/Practice.jsx'
import './App.css'

function App() {

  return (
    <>
      <p>Hello World!</p>
      <ChatProvider>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
        <Routes>
          <Route path="/test" element={<Practice />} />
        </Routes>
      </ChatProvider>
    </>
  )
}

export default App
