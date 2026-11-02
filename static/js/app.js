/**
 * 考 HSK Practice — Interactive Client Application
 * Handles View Routing, Quiz State Machine, Real-Time Countdown Timer,
 * Grading Engine, and Data Analytics Visualizations.
 */

// Application State
const state = {
  currentView: 'landing',     // 'landing' | 'learn'
  currentTab: 'exam',        // 'exam' | 'analytics' | 'history'
  examSubState: 'start',      // 'start' | 'exam' | 'result'
  
  // Exam Engine State
  selectedLevel: 1,
  questions: [],
  currentIndex: 0,
  userAnswers: {},            // { question_id: selected_option }
  
  // Timer State (3 minutes = 180 seconds)
  examDuration: 180,
  timeRemaining: 180,
  timerInterval: null,
  examStartTime: null,
  
  // Current Exam Result
  lastResult: null,
  
  // Cached Analytics & History
  analyticsData: null,
  historyData: []
};

// ==========================================
// View Routing & Navigation
// ==========================================
function toggleDrawer(open) {
  const drawer = document.getElementById('slide-drawer');
  const backdrop = document.getElementById('drawer-backdrop');
  const edgeTab = document.getElementById('edge-drawer-tab');
  
  const shouldOpen = (open !== undefined) ? open : !drawer.classList.contains('open');
  
  if (shouldOpen) {
    drawer.classList.add('open');
    backdrop.classList.add('active');
    if (edgeTab) edgeTab.style.opacity = '0';
  } else {
    drawer.classList.remove('open');
    backdrop.classList.remove('active');
    if (edgeTab) edgeTab.style.opacity = '1';
  }
}

// Close drawer on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    toggleDrawer(false);
  }
});

function switchView(viewName) {
  state.currentView = viewName;
  const landingEl = document.getElementById('view-landing');
  const learnEl = document.getElementById('view-learn');
  
  if (viewName === 'landing') {
    landingEl.classList.remove('hidden');
    learnEl.classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    landingEl.classList.add('hidden');
    learnEl.classList.remove('hidden');
    switchTab(state.currentTab);
  }
}

function switchTab(tabName) {
  state.currentTab = tabName;
  
  // Update sidebar & drawer active classes
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('nav-item-on');
    if (item.getAttribute('data-tab') === tabName || item.getAttribute('data-drawer-tab') === tabName) {
      item.classList.add('nav-item-on');
    }
  });
  
  // Show target tab container
  document.getElementById('tab-exam').classList.add('hidden');
  document.getElementById('tab-analytics').classList.add('hidden');
  document.getElementById('tab-history').classList.add('hidden');
  
  if (tabName === 'exam') {
    document.getElementById('tab-exam').classList.remove('hidden');
  } else if (tabName === 'analytics') {
    document.getElementById('tab-analytics').classList.remove('hidden');
    loadAnalytics();
  } else if (tabName === 'history') {
    document.getElementById('tab-history').classList.remove('hidden');
    loadHistory();
  }
}

// ==========================================
// Exam Engine & Timer
// ==========================================
async function startExam(level) {
  state.selectedLevel = level;
  state.examSubState = 'exam';
  state.currentIndex = 0;
  state.userAnswers = {};
  state.timeRemaining = state.examDuration;
  state.examStartTime = Date.now();
  
  const startCard = document.getElementById('exam-start-card');
  const runningCard = document.getElementById('exam-running-card');
  const resultCard = document.getElementById('exam-result-card');
  
  startCard.classList.add('hidden');
  resultCard.classList.add('hidden');
  runningCard.classList.remove('hidden');
  
  document.getElementById('exam-loading-spinner').classList.remove('hidden');
  document.getElementById('exam-question-box').classList.add('hidden');
  
  try {
    const res = await fetch(`/api/questions?level=${level}&count=8`);
    if (!res.ok) throw new Error('Failed to load questions');
    state.questions = await res.json();
    
    document.getElementById('exam-loading-spinner').classList.add('hidden');
    document.getElementById('exam-question-box').classList.remove('hidden');
    
    renderQuestionNavigator();
    renderCurrentQuestion();
    startTimer();
  } catch (err) {
    alert('เกิดข้อผิดพลาดในการดึงข้อสอบ กรุณาลองใหม่อีกครั้ง');
    resetExamToStart();
  }
}

function startTimer() {
  stopTimer();
  updateTimerDisplay();
  
  state.timerInterval = setInterval(() => {
    state.timeRemaining -= 1;
    updateTimerDisplay();
    
    if (state.timeRemaining <= 0) {
      stopTimer();
      alert('⏰ หมดเวลาทำข้อสอบแล้ว! ระบบจะส่งคำตอบโดยอัตโนมัติ');
      submitExam(true);
    }
  }, 1000);
}

function stopTimer() {
  if (state.timerInterval) {
    clearInterval(state.timerInterval);
    state.timerInterval = null;
  }
}

function updateTimerDisplay() {
  const timerEl = document.getElementById('exam-timer');
  const mins = Math.floor(Math.max(0, state.timeRemaining) / 60);
  const secs = String(Math.max(0, state.timeRemaining) % 60).padStart(2, '0');
  
  timerEl.innerText = `⏱ ${mins}:${secs}`;
  if (state.timeRemaining < 30) {
    timerEl.className = 'timer-warning text-base font-semibold';
  } else {
    timerEl.className = 'timer-normal text-base font-semibold';
  }
}

function renderQuestionNavigator() {
  const container = document.getElementById('question-navigator-pills');
  container.innerHTML = '';
  
  state.questions.forEach((q, idx) => {
    const pill = document.createElement('button');
    pill.innerText = idx + 1;
    pill.className = 'q-pill';
    
    if (idx === state.currentIndex) {
      pill.classList.add('q-pill-current');
    } else if (state.userAnswers[q.id] !== undefined) {
      pill.classList.add('q-pill-answered');
    }
    
    pill.onclick = () => jumpToQuestion(idx);
    container.appendChild(pill);
  });
}

function renderCurrentQuestion() {
  if (!state.questions.length || !state.questions[state.currentIndex]) return;
  const q = state.questions[state.currentIndex];
  
  // Update header info & progress
  document.getElementById('exam-question-meta').innerText = `ข้อ ${state.currentIndex + 1}/${state.questions.length} · ${q.part}`;
  const pct = ((state.currentIndex + 1) / state.questions.length) * 100;
  document.getElementById('exam-progress-bar').style.width = `${pct}%`;
  
  // Render question text & details
  document.getElementById('q-title').innerText = q.question;
  const pinyinEl = document.getElementById('q-pinyin');
  if (q.pinyin) {
    pinyinEl.innerText = q.pinyin;
    pinyinEl.classList.remove('hidden');
  } else {
    pinyinEl.classList.add('hidden');
  }
  
  // Render options
  const optionsContainer = document.getElementById('q-options-container');
  optionsContainer.innerHTML = '';
  
  const currentSelection = state.userAnswers[q.id];
  
  q.options.forEach((opt, optIdx) => {
    const choiceBtn = document.createElement('button');
    const letter = String.fromCharCode(65 + optIdx); // A, B, C, D
    choiceBtn.className = `choice ${currentSelection === opt ? 'choice-on' : ''}`;
    choiceBtn.innerHTML = `
      <span class="mr-3 font-semibold text-xs py-0.5 px-1.5 rounded bg-muted text-muted-foreground border">${letter}</span>
      <span class="flex-1">${opt}</span>
    `;
    choiceBtn.onclick = () => selectChoice(q.id, opt);
    optionsContainer.appendChild(choiceBtn);
  });
  
  // Update action buttons state
  const prevBtn = document.getElementById('btn-prev-q');
  const nextBtn = document.getElementById('btn-next-q');
  const submitBtn = document.getElementById('btn-submit-exam');
  
  prevBtn.disabled = (state.currentIndex === 0);
  
  const isLast = (state.currentIndex === state.questions.length - 1);
  if (isLast) {
    nextBtn.classList.add('hidden');
    submitBtn.classList.remove('hidden');
    const answeredCount = Object.keys(state.userAnswers).length;
    submitBtn.innerText = `ส่งคำตอบ (${answeredCount}/${state.questions.length})`;
  } else {
    nextBtn.classList.remove('hidden');
    submitBtn.classList.add('hidden');
  }
  
  renderQuestionNavigator();
}

function selectChoice(questionId, option) {
  state.userAnswers[questionId] = option;
  renderCurrentQuestion();
}

function prevQuestion() {
  if (state.currentIndex > 0) {
    state.currentIndex -= 1;
    renderCurrentQuestion();
  }
}

function nextQuestion() {
  if (state.currentIndex < state.questions.length - 1) {
    state.currentIndex += 1;
    renderCurrentQuestion();
  }
}

function jumpToQuestion(index) {
  if (index >= 0 && index < state.questions.length) {
    state.currentIndex = index;
    renderCurrentQuestion();
  }
}

async function submitExam(isAutoSubmit = false) {
  stopTimer();
  
  const answeredCount = Object.keys(state.userAnswers).length;
  const totalCount = state.questions.length;
  
  if (!isAutoSubmit && answeredCount < totalCount) {
    const confirmed = confirm(`คุณยังตอบไม่ครบ (ตอบแล้ว ${answeredCount} จาก ${totalCount} ข้อ) ต้องการส่งข้อสอบเลยหรือไม่?`);
    if (!confirmed) {
      startTimer();
      return;
    }
  }
  
  const submitBtn = document.getElementById('btn-submit-exam');
  submitBtn.disabled = true;
  submitBtn.innerText = 'กำลังตรวจข้อสอบ...';
  
  const timeSpent = Math.max(1, state.examDuration - state.timeRemaining);
  
  const payload = {
    level: state.selectedLevel,
    time_spent_seconds: timeSpent,
    answers: state.questions.map(q => ({
      question_id: q.id,
      selected_option: state.userAnswers[q.id] || null
    }))
  };
  
  try {
    const res = await fetch('/api/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error('Submission failed');
    const result = await res.json();
    state.lastResult = result;
    
    renderExamResults(result);
  } catch (err) {
    alert('เกิดข้อผิดพลาดในการส่งข้อสอบ กรุณาลองใหม่อีกครั้ง');
    submitBtn.disabled = false;
  }
}

function renderExamResults(result) {
  state.examSubState = 'result';
  document.getElementById('exam-running-card').classList.add('hidden');
  const resultCard = document.getElementById('exam-result-card');
  resultCard.classList.remove('hidden');
  
  // 1. Big score
  document.getElementById('result-big-score').innerText = result.score;
  document.getElementById('result-total-score').innerText = `/${result.total}`;
  document.getElementById('result-pct-badge').innerText = `${result.percentage}%`;
  
  // Praise message based on score
  const praiseEl = document.getElementById('result-praise-text');
  if (result.percentage >= 80) {
    praiseEl.innerText = '🎉 ยอดเยี่ยมมาก! คุณผ่านเกณฑ์การทดสอบอย่างสวยงาม';
    praiseEl.className = 'text-sm font-medium text-emerald-700';
  } else if (result.percentage >= 60) {
    praiseEl.innerText = '👍 ทำได้ดี! มีบางพาร์ทที่สามารถฝึกฝนเพิ่มเติมได้';
    praiseEl.className = 'text-sm font-medium text-amber-700';
  } else {
    praiseEl.innerText = '📚 ไม่เป็นไรนะ! ลองทบทวนคำศัพท์และไวยากรณ์แล้วสอบใหม่อีกครั้ง';
    praiseEl.className = 'text-sm font-medium text-rose-700';
  }
  
  // 2. Breakdown by part
  const partsGrid = document.getElementById('result-parts-grid');
  partsGrid.innerHTML = '';
  Object.entries(result.parts).forEach(([partName, [pScore, pTotal]]) => {
    const partPct = pTotal > 0 ? Math.round((pScore / pTotal) * 100) : 0;
    const card = document.createElement('div');
    card.className = 'p-3 bg-muted rounded-lg text-center border';
    card.innerHTML = `
      <p class="text-xs text-muted-foreground font-medium">${partName}</p>
      <p class="font-display text-xl text-foreground font-bold mt-1">${pScore}/${pTotal}</p>
      <p class="text-xs text-primary font-semibold">${partPct}%</p>
    `;
    partsGrid.appendChild(card);
  });
  
  // 3. Detailed questions review list
  const reviewList = document.getElementById('result-questions-list');
  reviewList.innerHTML = '';
  
  result.results.forEach((item, idx) => {
    const li = document.createElement('li');
    const isCorrect = item.is_correct;
    li.className = `p-4 rounded-lg border-l-4 bg-card border shadow-sm ${isCorrect ? 'border-l-emerald-600' : 'border-l-rose-600'}`;
    
    let answerStatusHtml = '';
    if (isCorrect) {
      answerStatusHtml = `<span class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">✓ ถูกต้อง</span>`;
    } else {
      answerStatusHtml = `<span class="inline-flex items-center gap-1 text-xs font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">✗ ตอบผิด</span>`;
    }
    
    li.innerHTML = `
      <div class="flex items-center justify-between gap-2">
        <span class="text-xs font-semibold text-muted-foreground">ข้อที่ ${idx + 1} · ${item.part}</span>
        ${answerStatusHtml}
      </div>
      <p class="font-display text-lg text-foreground font-semibold mt-2">${item.question}</p>
      ${item.pinyin ? `<p class="text-xs text-primary font-mono mb-2">${item.pinyin}</p>` : ''}
      <div class="mt-2 text-sm space-y-1">
        <p class="text-muted-foreground">
          คำตอบของคุณ: <span class="font-medium ${isCorrect ? 'text-emerald-700 font-semibold' : 'text-rose-600 line-through'}">${item.selected || '(ไม่ได้ตอบ)'}</span>
        </p>
        ${!isCorrect ? `
          <p class="text-foreground">
            เฉลยคำตอบที่ถูกต้อง: <span class="font-semibold text-emerald-700">${item.correct_answer}</span>
          </p>
        ` : ''}
      </div>
      ${item.explanation ? `
        <div class="mt-3 p-2.5 bg-muted/60 rounded text-xs text-muted-foreground border">
          <span class="font-semibold text-foreground">💡 คำอธิบาย:</span> ${item.explanation}
        </div>
      ` : ''}
    `;
    reviewList.appendChild(li);
  });
  
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function resetExamToStart() {
  stopTimer();
  state.examSubState = 'start';
  document.getElementById('exam-start-card').classList.remove('hidden');
  document.getElementById('exam-running-card').classList.add('hidden');
  document.getElementById('exam-result-card').classList.add('hidden');
  
  const submitBtn = document.getElementById('btn-submit-exam');
  submitBtn.disabled = false;
  submitBtn.innerText = 'ส่งคำตอบ';
}

// ==========================================
// Data Analytics Dashboard
// ==========================================
async function loadAnalytics() {
  const container = document.getElementById('analytics-content');
  container.innerHTML = '<p class="text-sm text-muted-foreground py-6 text-center">กำลังโหลดสถิติ...</p>';
  
  try {
    const res = await fetch('/api/analytics');
    if (!res.ok) throw new Error('Analytics fetch error');
    const data = await res.json();
    state.analyticsData = data;
    renderAnalytics(data);
  } catch (err) {
    container.innerHTML = '<p class="text-sm text-rose-600 text-center py-4">ไม่สามารถโหลดข้อมูลสถิติได้</p>';
  }
}

function renderAnalytics(data) {
  const container = document.getElementById('analytics-content');
  
  if (data.total_tests === 0) {
    container.innerHTML = `
      <div class="paper text-center py-10">
        <span class="text-3xl">📊</span>
        <h3 class="font-display text-xl text-foreground mt-3 font-semibold">ยังไม่มีข้อมูลสถิติ</h3>
        <p class="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
          ลองทำข้อสอบชุดแรกเพื่อเริ่มบันทึกคะแนนและวิเคราะห์จุดแข็ง-จุดอ่อนของคุณ
        </p>
        <button onclick="switchTab('exam')" class="btn-primary mt-5">เริ่มทำข้อสอบ</button>
      </div>
    `;
    return;
  }
  
  // Render metrics cards + Charts + Section breakdowns
  let recentBarsHtml = '';
  if (data.recent_scores && data.recent_scores.length > 0) {
    recentBarsHtml = `
      <div class="paper mt-6">
        <div class="flex items-center justify-between">
          <h2 class="font-display text-lg text-foreground font-semibold">คะแนนการสอบล่าสุด</h2>
          <span class="text-xs text-muted-foreground font-mono">12 ครั้งล่าสุด</span>
        </div>
        <div class="chart-bar-container mt-4">
          ${data.recent_scores.map(s => {
            const h = Math.max(6, Math.min(100, s.percentage));
            return `
              <div class="chart-bar-col" title="HSK ${s.level} · ${s.score}/${s.total} (${s.percentage}%)">
                <span class="text-[11px] font-mono text-muted-foreground">${Math.round(s.percentage)}%</span>
                <div class="chart-bar" style="height: ${h}%;"></div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }
  
  let partsHtml = '';
  if (data.parts_accuracy && Object.keys(data.parts_accuracy).length > 0) {
    partsHtml = `
      <div class="paper mt-6">
        <h2 class="font-display text-lg text-foreground font-semibold">ความแม่นยำแยกตามพาร์ท</h2>
        <p class="text-xs text-muted-foreground mt-0.5">วิเคราะห์สัดส่วนการตอบถูกในแต่ละมิติของข้อสอบ</p>
        <div class="mt-4 space-y-4">
          ${Object.entries(data.parts_accuracy).map(([partName, acc]) => `
            <div>
              <div class="flex items-center justify-between text-sm">
                <span class="font-medium text-foreground">${partName}</span>
                <span class="text-muted-foreground font-mono text-xs">${acc.score}/${acc.total} (${acc.percentage}%)</span>
              </div>
              <div class="progress-track mt-1.5">
                <div class="progress-fill" style="width: ${acc.percentage}%;"></div>
              </div>
            </div>
          `).join('')}
        </div>
        ${data.weakest_part ? `
          <div class="mt-5 p-3.5 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
            <span class="text-base">💡</span>
            <div>
              <span class="font-semibold">ข้อเสนอแนะในการพัฒนา:</span>
              คุณทำคะแนนพาร์ท <b class="underline">${data.weakest_part}</b> ได้น้อยที่สุด แนะนำให้เน้นทบทวนเนื้อหาส่วนนี้เพิ่มขึ้นในการสอบครั้งถัดไป
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }
  
  container.innerHTML = `
    <!-- Top 3 Metric Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div class="paper p-4">
        <p class="text-xs text-muted-foreground font-medium">สอบแล้ว</p>
        <p class="font-display text-3xl text-primary font-bold mt-1">${data.total_tests} <span class="text-sm font-normal text-muted-foreground">ครั้ง</span></p>
      </div>
      <div class="paper p-4">
        <p class="text-xs text-muted-foreground font-medium">คะแนนเฉลี่ย</p>
        <p class="font-display text-3xl text-primary font-bold mt-1">${data.average_score_pct}%</p>
      </div>
      <div class="paper p-4">
        <p class="text-xs text-muted-foreground font-medium">คะแนนสูงสุด</p>
        <p class="font-display text-3xl text-primary font-bold mt-1">${data.highest_score_pct}%</p>
      </div>
    </div>
    
    ${recentBarsHtml}
    ${partsHtml}
  `;
}

// ==========================================
// Exam History Table
// ==========================================
async function loadHistory() {
  const container = document.getElementById('history-content');
  container.innerHTML = '<p class="text-sm text-muted-foreground py-6 text-center">กำลังโหลดประวัติ...</p>';
  
  try {
    const res = await fetch('/api/attempts?limit=50');
    if (!res.ok) throw new Error('History fetch error');
    const attempts = await res.json();
    state.historyData = attempts;
    renderHistory(attempts);
  } catch (err) {
    container.innerHTML = '<p class="text-sm text-rose-600 text-center py-4">ไม่สามารถโหลดประวัติการสอบได้</p>';
  }
}

function renderHistory(attempts) {
  const container = document.getElementById('history-content');
  
  if (!attempts || attempts.length === 0) {
    container.innerHTML = `
      <div class="paper text-center py-10">
        <span class="text-3xl">🗂</span>
        <h3 class="font-display text-xl text-foreground mt-3 font-semibold">ยังไม่มีประวัติการสอบ</h3>
        <p class="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
          ประวัติการทำข้อสอบทุกครั้งจะถูกบันทึกและแสดงที่นี่
        </p>
        <button onclick="switchTab('exam')" class="btn-primary mt-5">ทำข้อสอบแรก</button>
      </div>
    `;
    return;
  }
  
  const rowsHtml = attempts.map(att => {
    const dateFormatted = new Date(att.created_at).toLocaleString('th-TH', {
      dateStyle: 'medium',
      timeStyle: 'short'
    });
    
    const mins = Math.floor(att.time_spent_seconds / 60);
    const secs = att.time_spent_seconds % 60;
    const timeFormatted = `${mins}m ${secs}s`;
    
    let badgeClass = 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (att.percentage < 60) {
      badgeClass = 'text-rose-700 bg-rose-50 border-rose-200';
    } else if (att.percentage < 80) {
      badgeClass = 'text-amber-700 bg-amber-50 border-amber-200';
    }
    
    return `
      <tr>
        <td class="text-foreground">${dateFormatted}</td>
        <td><span class="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-muted border">HSK ${att.level}</span></td>
        <td class="font-semibold text-foreground">${att.score} / ${att.total}</td>
        <td><span class="inline-block px-2 py-0.5 rounded text-xs font-semibold border ${badgeClass}">${att.percentage}%</span></td>
        <td class="text-muted-foreground font-mono text-xs">${timeFormatted}</td>
      </tr>
    `;
  }).join('');
  
  container.innerHTML = `
    <div class="paper overflow-hidden p-0">
      <div class="overflow-x-auto">
        <table class="exam-table">
          <thead>
            <tr>
              <th>วันที่-เวลา</th>
              <th>ระดับ</th>
              <th>คะแนน</th>
              <th>%</th>
              <th>เวลาที่ใช้</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

// ==========================================
// Application Bootstrap
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  // Bind level selector buttons
  document.querySelectorAll('.btn-level-choice').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.btn-level-choice').forEach(b => b.classList.remove('choice-on'));
      btn.classList.add('choice-on');
      state.selectedLevel = parseInt(btn.getAttribute('data-level'), 10);
    });
  });
});
