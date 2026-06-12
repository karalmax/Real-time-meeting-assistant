import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Send, MessageSquare, FileText, ClipboardList, Loader } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // New States for Summary & Server Processing Indicator
  const [summary, setSummary] = useState(null);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [isServerProcessing, setIsServerProcessing] = useState(false);

  const ws = useRef(null);
  const audioContext = useRef(null);
  const audioInput = useRef(null);
  const processor = useRef(null);
  const globalStream = useRef(null);

  const chatEndRef = useRef(null);
  const transcriptEndRef = useRef(null);

  // Auto-scroll for Chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, summary]);

  // Auto-scroll for Transcript when new text or loading state appears
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript, isServerProcessing]);

  const startRecording = async () => {
    try {
      ws.current = new WebSocket("ws://localhost:8000/ws/audio");

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.status === "success" && data.text) {
          setTranscript((prev) => prev + " " + data.text);
          setIsServerProcessing(false);
        } else if (data.status === "processing") {
          setIsServerProcessing(true);
        }
      };

      ws.current.onclose = () => setIsServerProcessing(false);
      ws.current.onerror = () => setIsServerProcessing(false);

      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true
      });
      globalStream.current = stream;

      audioContext.current = new window.AudioContext({ sampleRate: 16000 });
      audioInput.current = audioContext.current.createMediaStreamSource(stream);
      processor.current = audioContext.current.createScriptProcessor(4096, 1, 1);

      processor.current.onaudioprocess = (e) => {
        const float32Array = e.inputBuffer.getChannelData(0);
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
          int16Array[i] = Math.max(-32768, Math.min(32767, float32Array[i] * 32768));
        }
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(int16Array.buffer);
        }
      };

      audioInput.current.connect(processor.current);
      processor.current.connect(audioContext.current.destination);

      setIsRecording(true);
    } catch (error) {
      console.error("Error starting recording:", error);
      alert("Screen share access denied or audio not selected.");
    }
  };

  const stopRecording = () => {
    if (processor.current && audioContext.current) {
      processor.current.disconnect();
      audioInput.current.disconnect();
      audioContext.current.close();
    }
    if (globalStream.current) {
      globalStream.current.getTracks().forEach(track => track.stop());
    }
    if (ws.current) {
      ws.current.close();
    }
    setIsRecording(false);
    setIsServerProcessing(false);
  };

  const askQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userQ = question;
    setQuestion("");
    setChatHistory(prev => [...prev, { role: "user", text: userQ }]);
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userQ })
      });
      const data = await response.json();

      setChatHistory(prev => [...prev, { role: "ai", text: data.answer }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: "ai", text: "Error: Unable to connect to Intelligence Layer." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateMeetingSummary = async () => {
    setIsGeneratingSummary(true);
    try {
      const response = await fetch("http://localhost:8000/api/summary");
      const data = await response.json();
      setSummary(data.summary);
    } catch (error) {
      setSummary("Error: Could not generate meeting summary.");
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans p-6">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-blue-400 flex items-center gap-3">
            <MessageSquare className="w-8 h-8" />
            Real-Time Meeting Assistant
          </h1>
          <p className="text-gray-400 mt-2">Privacy-First Offline Intelligence</p>
        </div>
        <button
          onClick={generateMeetingSummary}
          disabled={isGeneratingSummary || transcript.length === 0}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
        >
          <ClipboardList className="w-5 h-5" />
          {isGeneratingSummary ? "Analyzing..." : "Generate MoM"}
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-140px)]">

        {/* LEFT: Live Transcript */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/50">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-green-400" /> Live Transcript
            </h2>
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${isRecording ? "bg-red-500/10 text-red-500 hover:bg-red-500/20" : "bg-blue-600 text-white hover:bg-blue-700"
                }`}
            >
              {isRecording ? <><MicOff className="w-5 h-5" /> Stop Listening</> : <><Mic className="w-5 h-5" /> Start Meeting</>}
            </button>
          </div>
          <div className="p-6 flex-1 overflow-y-auto leading-relaxed text-lg text-gray-300">
            {transcript ? (
              <span>{transcript}</span>
            ) : (
              <span className="text-gray-600 italic">Start the meeting to see live transcription here...</span>
            )}

            {isServerProcessing && (
              <div className="mt-4 flex items-center gap-3 px-4 py-3 bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 rounded-lg text-sm font-medium w-fit animate-pulse">
                <Loader className="w-5 h-5 animate-spin" />
                AI is processing audio (Google server busy, retrying)... ⏳ Don't close tab!
              </div>
            )}

            <div ref={transcriptEndRef} />
          </div>
        </div>

        {/* RIGHT: RAG Chat & Summary */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 flex flex-col overflow-hidden relative">
          <div className="p-4 border-b border-gray-800 bg-gray-900/50 flex justify-between items-center">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-purple-400" /> Intelligence Layer
            </h2>
            {summary && (
              <button
                onClick={() => setSummary(null)}
                className="text-sm text-gray-400 hover:text-white"
              >
                Close Summary
              </button>
            )}
          </div>

          <div className="flex-1 p-6 overflow-y-auto flex flex-col gap-4">
            
            {/* 1. Show Summary if it exists */}
            {summary && (
              <div className="bg-gray-800/80 p-6 rounded-xl border border-purple-500/30 text-gray-200 mb-4">
                <h3 className="text-2xl font-bold mb-4 text-purple-300 flex items-center gap-2">
                  <ClipboardList className="w-6 h-6" /> Meeting Minutes
                </h3>
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown>{summary}</ReactMarkdown>
                </div>
              </div>
            )}

            {/* 2. Always show Chat History below the summary */}
            {chatHistory.length === 0 && !summary && (
              <div className="m-auto text-gray-600 text-center">
                Ask questions about the ongoing meeting. <br /> "What was the budget discussed?"
              </div>
            )}
            
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] p-3 rounded-xl ${msg.role === "user" ? "bg-blue-600 text-white rounded-br-none" : "bg-gray-800 text-gray-200 rounded-bl-none border border-gray-700"
                  }`}>
                  {msg.text}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 text-gray-400 p-3 rounded-xl rounded-bl-none border border-gray-700 animate-pulse">
                  Analyzing context...
                </div>
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>

          {/* 3. ALWAYS show the Question Input Form (Removed !summary wrapper) */}
          <form onSubmit={askQuestion} className="p-4 border-t border-gray-800 flex gap-3">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask anything about the meeting..."
              className="flex-1 bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 text-gray-200 placeholder-gray-500"
            />
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg flex items-center justify-center transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}

export default App;