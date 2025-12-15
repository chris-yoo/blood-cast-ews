"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { fetchForecasts, fetchSupplySuggestion, type BloodShortage, type SupplySuggestionResponse } from "@/lib/mockData"
import { AlertTriangle, MessageSquare, FileText, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { marked } from "marked"

const severityColors = {
  관심: "bg-blue-50 border-blue-200 text-blue-800",
  주의: "bg-yellow-50 border-yellow-200 text-yellow-800",
  경계: "bg-orange-50 border-orange-200 text-orange-800",
  심각: "bg-red-50 border-red-200 text-red-800",
  정상: "bg-green-50 border-green-200 text-green-800",
}

const severityIcons = {
  관심: "🔵",
  주의: "🟡",
  경계: "🟠",
  심각: "🔴",
  정상: "✅",
}

const severityLabels = {
  관심: "관심 (Blue)",
  주의: "주의 (Yellow)",
  경계: "경계 (Orange)",
  심각: "심각 (Red)",
  정상: "정상 (Normal)",
}

export default function Home() {
  const router = useRouter()
  const [selectedShortage, setSelectedShortage] = useState<BloodShortage | null>(null)
  const [showReportModal, setShowReportModal] = useState(false)
  const [reportContent, setReportContent] = useState("")
  const [showSuggestionModal, setShowSuggestionModal] = useState(false)
  const [suggestionData, setSuggestionData] = useState<SupplySuggestionResponse | null>(null)
  const [loadingSuggestion, setLoadingSuggestion] = useState(false)
  const [loadingReport, setLoadingReport] = useState(false)
  const [shortages, setShortages] = useState<BloodShortage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastDate, setLastDate] = useState<string>("")

  useEffect(() => {
    async function loadForecasts() {
      try {
        setLoading(true)
        setError(null)
        const data = await fetchForecasts(true) // include_all=true로 모든 예측 포함
        setShortages(data.forecasts)
        setLastDate(data.lastDate)
      } catch (err) {
        console.error("Error loading forecasts:", err)
        setError("Failed to load forecasts. Please ensure the backend is running.")
      } finally {
        setLoading(false)
      }
    }
    loadForecasts()
  }, [])

  // Sort by severity: 심각 > 경계 > 주의 > 관심 > 정상
  const severityOrder = { '심각': 0, '경계': 1, '주의': 2, '관심': 3, '정상': 4 }
  
  const sortBySeverity = (a: BloodShortage, b: BloodShortage) => {
    const orderA = severityOrder[a.severity] ?? 999
    const orderB = severityOrder[b.severity] ?? 999
    return orderA - orderB
  }

  const shortagesByMonth = {
    1: shortages.filter(s => s.month === 1).sort(sortBySeverity),
    2: shortages.filter(s => s.month === 2).sort(sortBySeverity),
    3: shortages.filter(s => s.month === 3).sort(sortBySeverity),
  }

  const handleShortageClick = (shortage: BloodShortage) => {
    setSelectedShortage(shortage)
  }

  const handleChatWithAI = (shortage: BloodShortage) => {
    const params = new URLSearchParams({
      region: shortage.region,
      bloodType: shortage.bloodType,
      month: shortage.month.toString(),
    })
    router.push(`/chat?${params.toString()}`)
  }

  const handleGenerateReport = async (shortage: BloodShortage) => {
    setLoadingReport(true)
    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          region: shortage.region,
          bloodType: shortage.bloodType,
          month: shortage.month,
        }),
      })
      const data = await response.json()
      setReportContent(data.report || "Report generation failed. Please try again.")
      setShowReportModal(true)
    } catch (error) {
      console.error("Error generating report:", error)
      setReportContent("Error generating report. Please ensure the backend is running.")
      setShowReportModal(true)
    } finally {
      setLoadingReport(false)
    }
  }

  const handleSavePDF = () => {
    const printWindow = window.open("", "_blank")
    if (printWindow && selectedShortage) {
      // 마크다운을 HTML로 변환
      const htmlContent = marked(reportContent, {
        breaks: true,
        gfm: true,
      })
      
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="UTF-8">
            <title>Bloodcast Report - ${selectedShortage.region} ${selectedShortage.bloodType}형</title>
            <style>
              @media print {
                body { margin: 0; padding: 20px; }
                @page { margin: 2cm; }
              }
              body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: white;
              }
              .header {
                border-bottom: 3px solid #dc2626;
                padding-bottom: 16px;
                margin-bottom: 24px;
              }
              .header h1 {
                font-size: 28px;
                font-weight: bold;
                margin: 0 0 8px 0;
                color: #1a1a1a;
                border: none;
              }
              .meta {
                color: #666;
                font-size: 14px;
                margin-top: 8px;
              }
              .meta strong {
                color: #333;
              }
              h1 {
                font-size: 24px;
                font-weight: bold;
                margin-top: 24px;
                margin-bottom: 16px;
                color: #1a1a1a;
                border-bottom: 2px solid #dc2626;
                padding-bottom: 8px;
              }
              h2 {
                font-size: 20px;
                font-weight: bold;
                margin-top: 20px;
                margin-bottom: 12px;
                color: #1a1a1a;
              }
              h3 {
                font-size: 18px;
                font-weight: bold;
                margin-top: 16px;
                margin-bottom: 10px;
                color: #1a1a1a;
              }
              p {
                margin-bottom: 12px;
                line-height: 1.6;
                color: #333;
              }
              ul, ol {
                margin-bottom: 16px;
                padding-left: 24px;
              }
              li {
                margin-bottom: 8px;
                line-height: 1.6;
              }
              strong {
                font-weight: 600;
                color: #1a1a1a;
              }
              em {
                font-style: italic;
              }
              code {
                background-color: #f3f4f6;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
              }
              pre {
                background-color: #f3f4f6;
                padding: 12px;
                border-radius: 6px;
                overflow-x: auto;
                margin: 16px 0;
              }
              pre code {
                background: none;
                padding: 0;
              }
              blockquote {
                border-left: 4px solid #dc2626;
                padding-left: 16px;
                margin: 16px 0;
                font-style: italic;
                color: #666;
                background-color: #fef2f2;
                padding: 12px 16px;
              }
              hr {
                border: none;
                border-top: 1px solid #e5e7eb;
                margin: 24px 0;
              }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>혈액 공급 부족 분석 리포트</h1>
              <div class="meta">
                <strong>지역:</strong> ${selectedShortage.region} | 
                <strong>혈액형:</strong> ${selectedShortage.bloodType}형 | 
                <strong>예측 기간:</strong> ${selectedShortage.month}개월 후 | 
                <strong>경보 등급:</strong> ${selectedShortage.severity}
              </div>
            </div>
            ${htmlContent}
          </body>
        </html>
      `)
      printWindow.document.close()
      
      // 약간의 지연 후 인쇄 (스타일 로딩 대기)
      setTimeout(() => {
        printWindow.print()
      }, 250)
    }
  }

  const handleCopyText = () => {
    navigator.clipboard.writeText(reportContent)
    alert("Report copied to clipboard!")
  }

  const handleGetSuggestion = async (shortage: BloodShortage) => {
    try {
      setLoadingSuggestion(true)
      setShowSuggestionModal(true)
      const data = await fetchSupplySuggestion(shortage.region, shortage.bloodType, shortage.month)
      setSuggestionData(data)
    } catch (error) {
      console.error("Error fetching supply suggestions:", error)
      alert("조달 제안을 불러오는 중 오류가 발생했습니다.")
      setShowSuggestionModal(false)
    } finally {
      setLoadingSuggestion(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-red-600" />
          <p className="text-gray-600">Loading forecasts...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Blood Supply Forecast</h1>
        <p className="text-gray-600">
          Forecasted shortages for the next 1-3 months
          {lastDate && <span className="ml-2 text-sm">(Last data: {lastDate})</span>}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {[1, 2, 3].map((month) => (
          <div key={month}>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              {month} Month{month > 1 ? "s" : ""} Ahead
            </h2>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {shortagesByMonth[month as keyof typeof shortagesByMonth].map((shortage) => (
                <Card
                  key={shortage.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${severityColors[shortage.severity]} py-2`}
                  onClick={() => handleShortageClick(shortage)}
                >
                  <CardHeader className="pb-2 pt-3 px-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-semibold">
                        {shortage.region}
                      </CardTitle>
                      <span className="text-lg">{severityIcons[shortage.severity]}</span>
                    </div>
                    <CardDescription className="text-xs font-medium mt-1">
                      {shortage.bloodType}형
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="px-4 pb-3 pt-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs">
                        {shortage.severity !== '정상' && <AlertTriangle className="h-3 w-3" />}
                        <span className="font-medium">{severityLabels[shortage.severity]}</span>
                      </div>
                      {shortage.forecastValue && (
                        <div className="text-xs text-gray-600 font-medium">
                          {Math.round(shortage.forecastValue).toLocaleString()}건
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
              {shortagesByMonth[month as keyof typeof shortagesByMonth].length === 0 && (
                <Card className="bg-green-50 border-green-200 py-4">
                  <CardContent className="pt-2">
                    <p className="text-center text-green-800 text-sm">No shortages forecasted</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        ))}
      </div>

      {selectedShortage && (
        <Card className="fixed inset-x-4 bottom-4 md:inset-x-auto md:left-72 md:right-4 md:bottom-4 md:max-w-md shadow-lg z-50">
          <CardHeader>
            <CardTitle>Shortage Details</CardTitle>
            <CardDescription>
              {selectedShortage.region} - Type {selectedShortage.bloodType} ({selectedShortage.month} month{selectedShortage.month > 1 ? "s" : ""} ahead)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              className="w-full"
              onClick={() => handleChatWithAI(selectedShortage)}
            >
              <MessageSquare className="mr-2 h-4 w-4" />
              Chat with AI
            </Button>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => handleGenerateReport(selectedShortage)}
              disabled={loadingReport}
            >
              {loadingReport ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileText className="mr-2 h-4 w-4" />
                  Generate Report
                </>
              )}
            </Button>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => handleGetSuggestion(selectedShortage)}
            >
              <MessageSquare className="mr-2 h-4 w-4" />
              조달 제안
            </Button>
            <Button
              variant="ghost"
              className="w-full"
              onClick={() => setSelectedShortage(null)}
            >
              Close
            </Button>
          </CardContent>
        </Card>
      )}

      {showReportModal && selectedShortage && (
        <div className="fixed inset-0 bg-white/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="max-w-3xl w-full max-h-[85vh] flex flex-col">
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>생성된 리포트</CardTitle>
                  <CardDescription className="mt-1">
                    {selectedShortage.region} {selectedShortage.bloodType}형 - {selectedShortage.month}개월 후 예측
                  </CardDescription>
        </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowReportModal(false)}
                  className="h-8 w-8"
                >
                  ×
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-6">
              <div className="markdown-content text-sm">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ node, ...props }) => <h1 className="text-xl font-bold mb-4 mt-4 text-gray-900 border-b-2 border-red-200 pb-2" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-lg font-bold mb-3 mt-4 text-gray-900" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-base font-bold mb-2 mt-3 text-gray-900" {...props} />,
                    p: ({ node, ...props }) => <p className="mb-3 last:mb-0 leading-relaxed text-gray-800" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc list-outside mb-3 ml-5 space-y-1.5" {...props} />,
                    ol: ({ node, ...props }) => <ol className="list-decimal list-outside mb-3 ml-5 space-y-1.5" {...props} />,
                    li: ({ node, ...props }) => <li className="ml-2 leading-relaxed" {...props} />,
                    strong: ({ node, ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
                    em: ({ node, ...props }) => <em className="italic" {...props} />,
                    code: ({ node, inline, ...props }: any) => 
                      inline ? (
                        <code className="bg-gray-200 px-1.5 py-0.5 rounded text-xs font-mono text-gray-800" {...props} />
                      ) : (
                        <code className="block bg-gray-200 p-3 rounded text-xs font-mono overflow-x-auto my-2 text-gray-800" {...props} />
                      ),
                    blockquote: ({ node, ...props }) => (
                      <blockquote className="border-l-4 border-red-300 pl-4 italic my-3 text-gray-700 bg-red-50 py-2" {...props} />
                    ),
                    hr: ({ node, ...props }) => <hr className="my-4 border-gray-300" {...props} />,
                  }}
                >
                  {reportContent}
                </ReactMarkdown>
              </div>
            </CardContent>
            <div className="border-t p-4 flex gap-2">
              <Button onClick={handleSavePDF} className="flex-1">
                <FileText className="mr-2 h-4 w-4" />
                PDF로 저장
              </Button>
              <Button variant="outline" onClick={handleCopyText}>
                텍스트 복사
              </Button>
            </div>
          </Card>
        </div>
      )}

      {showSuggestionModal && (
        <div className="fixed inset-0 bg-white/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="max-w-3xl w-full max-h-[85vh] flex flex-col">
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>조달 제안</CardTitle>
                  <CardDescription className="mt-1">
                    {selectedShortage?.region} {selectedShortage?.bloodType}형 - {selectedShortage?.month}개월 후
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    setShowSuggestionModal(false)
                    setSuggestionData(null)
                  }}
                  className="h-8 w-8"
                >
                  ×
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-6">
              {loadingSuggestion ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-red-600 mr-2" />
                  <p className="text-gray-600">조달 제안을 생성하는 중...</p>
                </div>
              ) : suggestionData ? (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-900 mb-2">부족 현황</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">예측값:</span>
                        <span className="ml-2 font-semibold">{Math.round(suggestionData.forecastValue).toLocaleString()}건</span>
                      </div>
                      <div>
                        <span className="text-gray-600">기준선:</span>
                        <span className="ml-2 font-semibold">{Math.round(suggestionData.baseline).toLocaleString()}건</span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-gray-600">부족량:</span>
                        <span className="ml-2 font-semibold text-red-600">
                          {Math.round(suggestionData.shortageAmount).toLocaleString()}건
                        </span>
                      </div>
                    </div>
                  </div>

                  {suggestionData.suggestions.length > 0 ? (
                    <>
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-3">조달 제안</h3>
                        <div className="space-y-2">
                          {suggestionData.suggestions.map((suggestion, index) => (
                            <Card key={index} className="border-l-4 border-l-green-500">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div className="flex-1">
                                    <div className="font-semibold text-gray-900">
                                      {suggestion.sourceRegion}
                                    </div>
                                    <div className="text-sm text-gray-600 mt-1">
                                      거리: {suggestion.distance.toFixed(1)}km
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-lg font-bold text-green-600">
                                      {Math.round(suggestion.amount).toLocaleString()}건
                                    </div>
                                    <div className="text-xs text-gray-500">
                                      {suggestion.bloodType}형
                                    </div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-green-900">총 조달 가능량:</span>
                          <span className="text-lg font-bold text-green-600">
                            {Math.round(suggestionData.totalSuggested).toLocaleString()}건
                          </span>
                        </div>
                        {suggestionData.totalSuggested < suggestionData.shortageAmount && (
                          <p className="text-sm text-orange-600 mt-2">
                            ⚠️ 부족량의 일부만 조달 가능합니다. ({Math.round((suggestionData.totalSuggested / suggestionData.shortageAmount) * 100)}%)
                          </p>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-600 mb-2">조달 가능한 지역을 찾을 수 없습니다.</p>
                      <p className="text-sm text-gray-500">
                        같은 혈액형을 가진 다른 지역에 여유가 없거나, 거리가 너무 멀어 조달이 어렵습니다.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  데이터를 불러올 수 없습니다.
                </div>
              )}
            </CardContent>
            <div className="border-t p-4">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setShowSuggestionModal(false)
                  setSuggestionData(null)
                }}
              >
                닫기
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
