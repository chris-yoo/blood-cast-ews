"use client"

import { useState, useEffect, useRef, Suspense } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { fetchRegions, fetchBloodTypes } from "@/lib/mockData"
import { Send, Bot, User, Loader2 } from "lucide-react"
import { useSearchParams } from "next/navigation"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface Message {
  role: "user" | "assistant"
  content: string
}

function ChatContent() {
  const searchParams = useSearchParams()
  const [selectedRegion, setSelectedRegion] = useState("")
  const [selectedBloodType, setSelectedBloodType] = useState("")
  const [selectedMonth, setSelectedMonth] = useState(1)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [regions, setRegions] = useState<string[]>([])
  const [bloodTypes, setBloodTypes] = useState<string[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    async function loadData() {
      try {
        setLoadingData(true)
        const [regionsData, bloodTypesData] = await Promise.all([
          fetchRegions(),
          fetchBloodTypes()
        ])
        setRegions(regionsData)
        setBloodTypes(bloodTypesData)
      } catch (error) {
        console.error("Error loading regions/blood types:", error)
      } finally {
        setLoadingData(false)
      }
    }
    loadData()
  }, [])

  useEffect(() => {
    const region = searchParams.get("region")
    const bloodType = searchParams.get("bloodType")
    const month = searchParams.get("month")

    if (region && bloodType) {
      setSelectedRegion(region)
      setSelectedBloodType(bloodType)
      if (month) {
        setSelectedMonth(parseInt(month, 10))
      }
      const initialMessage = `${region} ${bloodType}형이 ${month || 1}개월 후 부족할 것으로 예측되는 이유를 알려주세요.`
      setInput(initialMessage)
    }
  }, [searchParams])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    if (!selectedRegion || !selectedBloodType) {
      alert("지역과 혈액형을 먼저 선택해주세요.")
      return
    }

    const messageText = input.trim()
    const userMessage: Message = { role: "user", content: messageText }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: messageText,
          region: selectedRegion,
          bloodType: selectedBloodType,
          month: selectedMonth,
        }),
      })

      const data = await response.json()
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response || "Sorry, I couldn't generate a response. Please try again.",
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("Error sending message:", error)
      const errorMessage: Message = {
        role: "assistant",
        content: "Error connecting to the AI service. Please ensure the backend is running.",
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  if (loadingData) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-red-600" />
          <p className="text-gray-600">Loading data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Chat AI</h1>
        <p className="text-gray-600">Ask questions about blood supply forecasts</p>
      </div>

      <div className="mb-4 flex gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            지역 (Region)
          </label>
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="">지역 선택</option>
            {regions.map((region) => (
              <option key={region} value={region}>
                {region}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            혈액형 (Blood Type)
          </label>
          <select
            value={selectedBloodType}
            onChange={(e) => setSelectedBloodType(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="">혈액형 선택</option>
            {bloodTypes.map((type) => (
              <option key={type} value={type}>
                {type}형
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            예측 기간 (Month)
          </label>
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(parseInt(e.target.value, 10))}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value={1}>1개월 후</option>
            <option value={2}>2개월 후</option>
            <option value={3}>3개월 후</option>
          </select>
        </div>
      </div>

      <Card className="flex-1 flex flex-col mb-4">
        <CardHeader>
          <CardTitle>Conversation</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              지역과 혈액형을 선택한 후 질문을 입력하세요.
            </div>
          )}
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.role === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                  <Bot className="h-5 w-5 text-red-600" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === "user"
                    ? "bg-red-600 text-white"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                {message.role === "assistant" ? (
                  <div className="text-sm markdown-content">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({ node, ...props }) => <h1 className="text-lg font-bold mb-3 mt-3 text-gray-900" {...props} />,
                        h2: ({ node, ...props }) => <h2 className="text-base font-bold mb-2 mt-3 text-gray-900" {...props} />,
                        h3: ({ node, ...props }) => <h3 className="text-sm font-bold mb-2 mt-2 text-gray-900" {...props} />,
                        p: ({ node, ...props }) => <p className="mb-3 last:mb-0 leading-relaxed text-gray-800" {...props} />,
                        ul: ({ node, ...props }) => <ul className="list-disc list-outside mb-3 ml-4 space-y-1.5" {...props} />,
                        ol: ({ node, ...props }) => <ol className="list-decimal list-outside mb-3 ml-4 space-y-1.5" {...props} />,
                        li: ({ node, ...props }) => <li className="ml-2 leading-relaxed" {...props} />,
                        strong: ({ node, ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
                        em: ({ node, ...props }) => <em className="italic" {...props} />,
                        code: ({ node, inline, ...props }: any) => 
                          inline ? (
                            <code className="bg-gray-200 px-1.5 py-0.5 rounded text-xs font-mono text-gray-800" {...props} />
                          ) : (
                            <code className="block bg-gray-200 p-2 rounded text-xs font-mono overflow-x-auto my-2 text-gray-800" {...props} />
                          ),
                        blockquote: ({ node, ...props }) => (
                          <blockquote className="border-l-4 border-gray-400 pl-4 italic my-3 text-gray-700" {...props} />
                        ),
                        hr: ({ node, ...props }) => <hr className="my-4 border-gray-300" {...props} />,
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                )}
              </div>
              {message.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                  <User className="h-5 w-5 text-gray-600" />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                <Bot className="h-5 w-5 text-red-600" />
              </div>
              <div className="bg-gray-100 rounded-lg px-4 py-2">
                <p className="text-sm text-gray-500">Thinking...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSend()}
          placeholder="혈액 공급에 대해 질문하세요..."
          className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
          disabled={isLoading}
        />
        <Button onClick={handleSend} disabled={isLoading || !input.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="p-8">Loading...</div>}>
      <ChatContent />
    </Suspense>
  )
}

