import { computed, reactive, ref } from 'vue'
import { demoHistory, demoQuestions, failedReturnTests } from '../mockData'
import type { DemoQuestion, ProblemPanelMode, QuestionStatus, SubmitRecord, TestCaseRecord } from '../types'

interface DemoState {
  questions: DemoQuestion[]
  history: SubmitRecord[]
  activeQuestionId: string
  panelMode: ProblemPanelMode
  sidebarCollapsed: boolean
  feedbackExpanded: boolean
}

const toastRecord = ref<SubmitRecord | null>(null)

const state = reactive<DemoState>({
  questions: demoQuestions.map((question) => ({ ...question })),
  history: [...demoHistory],
  activeQuestionId: demoQuestions[0]?.id || '',
  panelMode: 'description',
  sidebarCollapsed: false,
  feedbackExpanded: true,
})

const activeQuestion = computed(() => state.questions.find((question) => question.id === state.activeQuestionId) || state.questions[0])
const activeHistory = computed(() => state.history.filter((record) => record.questionId === state.activeQuestionId).slice().reverse())
const latestRecord = computed(() => activeHistory.value[0])
const latestRecordsByQuestion = computed(() => {
  const result: Record<string, SubmitRecord> = {}
  for (const record of state.history) {
    result[record.questionId] = record
  }
  return result
})

function selectQuestion(questionId: string) {
  state.activeQuestionId = questionId
  state.panelMode = 'description'
  state.feedbackExpanded = true
}

function setPanelMode(mode: ProblemPanelMode) {
  state.panelMode = mode
}

function toggleSidebar() {
  state.sidebarCollapsed = !state.sidebarCollapsed
}

function toggleFeedback() {
  state.feedbackExpanded = !state.feedbackExpanded
}

function updateDraft(value: string) {
  const question = activeQuestion.value
  if (!question) return
  question.answerDraft = value
  if (question.status === 'not_started') question.status = 'draft'
}

function toggleChoice(option: string) {
  const question = activeQuestion.value
  if (!question) return
  if (question.type === 'multiple_choice') {
    const selected = new Set(question.answerDraft.split('\n').filter(Boolean))
    if (selected.has(option)) selected.delete(option)
    else selected.add(option)
    updateDraft(Array.from(selected).join('\n'))
    return
  }
  updateDraft(option)
}

function buildTestCases(question: DemoQuestion, status: Exclude<QuestionStatus, 'not_started' | 'draft'>): TestCaseRecord[] {
  if (question.type === 'code') {
    return status === 'failed'
      ? failedReturnTests
      : failedReturnTests.map((testCase) => ({ ...testCase, actual: testCase.expected, passed: true, note: undefined }))
  }
  return [
    {
      name: question.type === 'multiple_choice' ? '选项完整性' : '选项检查',
      input: question.answerDraft || '未选择',
      expected: status === 'passed' ? question.answerDraft || '已选择' : '正确选项集合',
      actual: question.answerDraft || '空答案',
      passed: status === 'passed',
      note: status === 'failed' ? '当前选择不完整或为空。' : undefined,
    },
  ]
}

function appendRecord(action: 'run' | 'submit', status: Exclude<QuestionStatus, 'not_started' | 'draft'>, message: string) {
  const question = activeQuestion.value
  if (!question) return
  const testCases = buildTestCases(question, status)
  const record: SubmitRecord = {
    id: `${Date.now()}-${action}`,
    questionId: question.id,
    action,
    status,
    message,
    createdAt: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    testCases,
    runCases: action === 'run' ? testCases : undefined,
    terminalOutput: action === 'run' ? testCases.map((c) => `>>> ${question.functionName || 'main'}(${c.input})\n${c.actual}${c.error ? `\n${c.error}` : ''}`).join('\n\n') : undefined,
    failure_types: status === 'failed' ? ['答案错误'] : undefined,
  }
  state.history.push(record)
  state.panelMode = 'status'
  state.feedbackExpanded = true
  if (action === 'submit') toastRecord.value = record
}

function runCurrentQuestion() {
  const question = activeQuestion.value
  const hasDraft = Boolean(question?.answerDraft.trim())
  appendRecord('run', hasDraft ? 'passed' : 'failed', hasDraft ? '运行完成' : '运行失败')
}

function submitCurrentQuestion() {
  const question = activeQuestion.value
  const hasDraft = Boolean(question?.answerDraft.trim())
  appendRecord('submit', hasDraft ? 'passed' : 'failed', hasDraft ? '通过' : '未通过')
}

export function useDemoStore() {
  return {
    state,
    activeQuestion,
    activeHistory,
    latestRecord,
    latestRecordsByQuestion,
    selectQuestion,
    setPanelMode,
    toggleSidebar,
    toggleFeedback,
    updateDraft,
    toggleChoice,
    runCurrentQuestion,
    submitCurrentQuestion,
    toastRecord,
  }
}
