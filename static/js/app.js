function app() {
    return {
        route: window.location.pathname,
        skills: [],
        progress: null,
        reviewCount: 0,
        toast: null,
        toastType: 'error',
        achievementModal: null,
        darkMode: localStorage.getItem('darkMode') === 'true',

        async init() {
            window.addEventListener('popstate', () => {
                this.route = window.location.pathname;
            });
            this.applyDarkMode();
            await this.refresh();
        },

        toggleDark() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('darkMode', this.darkMode);
            this.applyDarkMode();
        },

        applyDarkMode() {
            document.documentElement.classList.toggle('dark', this.darkMode);
        },

        navigate(path) {
            window.history.pushState({}, '', path);
            this.route = path;
            // Refresh global data when returning to dashboard, refresh navbar for other views
            if (path === '/') this.refresh();
            else this.refreshNavbar();
            window.scrollTo(0, 0);
        },

        async refresh() {
            try {
                const [skills, progress, review] = await Promise.all([
                    API.get('/skills'),
                    API.get('/progress'),
                    API.get('/review/queue').catch(() => ({ cards: [] })),
                ]);
                this.skills = skills;
                this.progress = progress;
                this.reviewCount = review.cards?.length || 0;
            } catch (e) {
                // Silent on refresh — non-critical
            }
        },

        // Lightweight navbar update (no skills reload)
        async refreshNavbar() {
            try {
                const [progress, review] = await Promise.all([
                    API.get('/progress'),
                    API.get('/review/queue').catch(() => ({ cards: [] })),
                ]);
                this.progress = progress;
                this.reviewCount = review.cards?.length || 0;
            } catch (e) {
                // Silent
            }
        },

        showToast(message, type = 'error') {
            this.toast = message;
            this.toastType = type;
            setTimeout(() => { this.toast = null; }, 5000);
        },

        showAchievement(achievement) {
            this.achievementModal = achievement;
            setTimeout(() => { this.achievementModal = null; }, 4000);
        },

        xpForNextLevel(level) {
            return Math.round(100 * Math.pow(level + 1, 1.5));
        },

        xpProgress(progress) {
            const currentLevelXp = Math.round(100 * Math.pow(progress.level, 1.5));
            const nextLevelXp = this.xpForNextLevel(progress.level);
            const range = nextLevelXp - currentLevelXp;
            const current = progress.total_xp - currentLevelXp;
            return Math.min(100, Math.max(0, (current / range) * 100));
        },
    };
}

function skillPicker() {
    return {
        skillName: '',
        loading: false,
        curriculum: null,
        error: null,
        suggestions: [
            'Python Programming', 'Spanish Language', 'Guitar Basics',
            'Machine Learning', 'Digital Photography', 'Public Speaking',
            'JavaScript', 'Drawing & Sketching', 'Chess Strategy',
        ],

        initPicker() {
            this.curriculum = null;
            this.error = null;
            this.skillName = '';
        },

        async generateCurriculum() {
            if (!this.skillName.trim()) return;
            this.loading = true;
            this.error = null;
            this.curriculum = null;
            try {
                this.curriculum = await API.post('/skills/preview', { name: this.skillName.trim() });
            } catch (e) {
                this.error = e.message || 'Failed to generate curriculum. Please try again.';
            } finally {
                this.loading = false;
            }
        },

        async startLearning() {
            try {
                const skill = await API.post('/skills', {
                    name: this.curriculum.name,
                    description: this.curriculum.description,
                    curriculum: this.curriculum.topics,
                });
                window._navigate('/skills/' + skill.id);
            } catch (e) {
                this.error = e.message || 'Failed to create skill. Please try again.';
            }
        },
    };
}

function skillDetail() {
    return {
        skill: null,
        lessons: [],
        loadingLesson: false,
        completedCount: 0,
        error: null,
        showDeleteConfirm: false,
        deleting: false,

        // Cheat Sheet
        cheatSheetOpen: false,
        cheatSheetContent: null,
        cheatSheetRendered: '',
        cheatSheetError: null,
        loadingCheatSheet: false,
        copied: false,

        // Final Project
        projectData: null,
        projectLoading: false,
        projectError: null,
        projectSubmission: '',
        projectSubmitting: false,
        projectResult: null,
        projectPreviousPasses: false,
        projectEditor: null,

        async loadSkill() {
            const id = window.location.pathname.match(/\/skills\/(\d+)/)?.[1];
            if (!id) return;
            // Reset state for new skill
            this.skill = null;
            this.error = null;
            this.projectData = null;
            this.projectLoading = false;
            this.projectError = null;
            this.projectResult = null;
            this.projectPreviousPasses = false;
            this.cheatSheetContent = null;
            this.cheatSheetRendered = '';
            this.cheatSheetError = null;
            this.cheatSheetOpen = false;
            try {
                const data = await API.get('/skills/' + id);
                this.skill = data.skill;
                this.lessons = data.lessons || [];
                this.completedCount = this.lessons.filter(l => l.status === 'completed').length;
            } catch (e) {
                this.error = 'Failed to load skill. It may have been deleted.';
            }
        },

        async startLesson(lesson, index) {
            if (lesson.content_json) {
                window._navigate('/lessons/' + lesson.id);
                return;
            }
            this.loadingLesson = true;
            this.error = null;
            try {
                const generated = await API.post('/lessons/generate', {
                    skill_id: this.skill.id,
                    lesson_id: lesson.id,
                });
                window._navigate('/lessons/' + generated.id);
            } catch (e) {
                this.error = 'Failed to generate lesson. Please try again.';
            } finally {
                this.loadingLesson = false;
            }
        },

        async deleteSkill() {
            this.deleting = true;
            try {
                await API.post('/skills/' + this.skill.id + '/delete', {});
                window._navigate('/');
                window._refresh();
            } catch (e) {
                this.error = 'Failed to delete skill. Please try again.';
            } finally {
                this.deleting = false;
                this.showDeleteConfirm = false;
            }
        },

        async openCheatSheet() {
            this.cheatSheetOpen = true;
            this.cheatSheetError = null;
            if (this.cheatSheetContent) return;
            this.loadingCheatSheet = true;
            try {
                const data = await API.get('/skills/' + this.skill.id + '/cheatsheet');
                this.cheatSheetContent = data.content;
                this.cheatSheetRendered = marked.parse(data.content);
            } catch (e) {
                this.cheatSheetError = e.message || 'Failed to generate cheat sheet.';
            } finally {
                this.loadingCheatSheet = false;
            }
        },

        async regenerateCheatSheet() {
            this.loadingCheatSheet = true;
            this.cheatSheetError = null;
            try {
                const data = await API.post('/skills/' + this.skill.id + '/cheatsheet/regenerate', {});
                this.cheatSheetContent = data.content;
                this.cheatSheetRendered = marked.parse(data.content);
            } catch (e) {
                this.cheatSheetError = e.message || 'Failed to regenerate.';
            } finally {
                this.loadingCheatSheet = false;
            }
        },

        copyCheatSheet() {
            if (!this.cheatSheetContent) return;
            navigator.clipboard.writeText(this.cheatSheetContent).then(() => {
                this.copied = true;
                setTimeout(() => { this.copied = false; }, 2000);
            });
        },

        async loadProject() {
            if (!this.skill) return;
            this.projectLoading = true;
            this.projectError = null;
            try {
                this.projectData = await API.get('/skills/' + this.skill.id + '/project');
                if (this.projectData && this.projectData.id) {
                    const subs = await API.get('/projects/' + this.projectData.id + '/submissions');
                    this.projectPreviousPasses = subs.some(s => s.passed);
                }
            } catch (e) {
                this.projectError = e.message || 'Failed to load project.';
            } finally {
                this.projectLoading = false;
            }
        },

        initProjectEditor(el) {
            if (this.projectEditor) return;
            const editor = ace.edit(el);
            const isDark = document.documentElement.classList.contains('dark');
            editor.setTheme(isDark ? 'ace/theme/monokai' : 'ace/theme/chrome');
            editor.session.setMode('ace/mode/python');
            editor.setOptions({
                fontSize: '14px',
                showPrintMargin: false,
                tabSize: 4,
                useSoftTabs: true,
                wrap: true,
                minLines: 10,
                maxLines: 40,
            });
            editor.setValue('# Write your project code here\n', -1);
            this.projectEditor = editor;
        },

        async submitProject() {
            if (!this.projectData || this.projectSubmitting) return;
            const submission = this.projectData.submission_type === 'code'
                ? (this.projectEditor?.getValue() || '')
                : this.projectSubmission;
            if (!submission.trim()) return;
            this.projectSubmitting = true;
            this.projectResult = null;
            try {
                const result = await API.post('/projects/' + this.projectData.id + '/submit', {
                    project_id: this.projectData.id,
                    submission,
                });
                this.projectResult = result;
                if (result.xp_earned > 0) {
                    window._showToast('+' + result.xp_earned + ' XP — Project Complete! 🎉', 'success');
                    window._refreshNavbar();
                    this.projectPreviousPasses = true;
                }
            } catch (e) {
                this.projectResult = { error: e.message || 'Failed to evaluate submission.' };
            } finally {
                this.projectSubmitting = false;
            }
        },
    };
}

function lessonView() {
    return {
        lesson: null,
        lessonId: null,
        content: null,
        renderedContent: '',
        loading: true,
        quizLoading: false,
        error: null,
        alreadyCompleted: false,
        exercises: [],
        exerciseStates: {},
        editors: {},
        _saveTimers: {},
        currentExerciseIndex: 0,

        // Feedback
        feedbackModalOpen: false,
        feedbackTags: [],
        feedbackMessage: '',
        feedbackSubmitting: false,
        feedbackSubmitted: false,
        feedbackError: null,
        feedbackTagOptions: [
            { value: 'incorrect',        label: 'Incorrect info' },
            { value: 'unclear',          label: 'Unclear' },
            { value: 'too-basic',        label: 'Too basic' },
            { value: 'too-advanced',     label: 'Too advanced' },
            { value: 'missing-examples', label: 'Missing examples' },
            { value: 'great',            label: 'Great content \u2713' },
        ],

        // Explain it differently
        altExplanation: null,
        altExplanationLoading: false,
        altExplanationOpen: false,
        altExplanationError: null,

        _exerciseKey(index) {
            return 'exercise_draft_' + this.lessonId + '_' + index;
        },

        async loadLesson() {
            const id = window.location.pathname.match(/\/lessons\/(\d+)/)?.[1];
            if (!id) return;
            this.lessonId = id;
            this.loading = true;
            this.error = null;
            this.exercises = [];
            this.exerciseStates = {};
            this.editors = {};
            this.currentExerciseIndex = 0;
            try {
                this.lesson = await API.get('/lessons/' + id);
                if (this.lesson.error) throw new Error(this.lesson.error);
                this.alreadyCompleted = this.lesson.status === 'completed';
                this.content = JSON.parse(this.lesson.content_json || '{}');
                this.renderedContent = this.renderLessonContent(this.content);
                this.exercises = this.content.exercises || [];
                for (let i = 0; i < this.exercises.length; i++) {
                    const savedText = localStorage.getItem(this._exerciseKey(i)) || '';
                    this.exerciseStates[i] = { output: null, feedback: null, hints: [], correct: null, running: false, submitting: false, text: savedText };
                }
                const fb = await API.get('/lessons/' + id + '/feedback').catch(() => null);
                if (fb?.submitted) this.feedbackSubmitted = true;
            } catch (e) {
                this.error = e.message || 'Failed to load lesson.';
            } finally {
                this.loading = false;
            }
        },

        initEditor(index, el) {
            if (this.editors[index]) return;
            const editor = ace.edit(el);
            const isDark = document.documentElement.classList.contains('dark');
            editor.setTheme(isDark ? 'ace/theme/monokai' : 'ace/theme/chrome');
            editor.session.setMode('ace/mode/python');
            editor.setOptions({
                fontSize: '14px',
                showPrintMargin: false,
                tabSize: 4,
                useSoftTabs: true,
                wrap: true,
                minLines: 5,
                maxLines: 25,
            });
            const saved = localStorage.getItem(this._exerciseKey(index));
            const starter = saved || this.exercises[index]?.starter_code || '# Write your code here\n';
            editor.setValue(starter, -1);
            this.editors[index] = editor;

            editor.session.on('change', () => {
                clearTimeout(this._saveTimers[index]);
                this._saveTimers[index] = setTimeout(() => {
                    localStorage.setItem(this._exerciseKey(index), editor.getValue());
                }, 500);
            });
        },

        async runCode(index) {
            const state = this.exerciseStates[index];
            if (!state || state.running) return;
            state.running = true;
            state.output = null;

            try {
                const code = this.editors[index]?.getValue() || '';
                const result = await API.post('/exercises/run', { code });
                state.output = result.output || '(No output)';
            } catch (e) {
                state.output = 'Error: ' + (e.message || 'Failed to run code');
            } finally {
                state.running = false;
            }
        },

        async submitExercise(index) {
            const state = this.exerciseStates[index];
            if (!state || state.submitting) return;
            state.submitting = true;
            state.feedback = null;

            const ex = this.exercises[index];
            let submission = '';
            if (ex.type === 'code') {
                submission = this.editors[index]?.getValue() || '';
            } else {
                submission = state.text || '';
            }

            try {
                const result = await API.post('/exercises/evaluate', {
                    exercise: ex,
                    submission: submission,
                    output: state.output || null,
                });
                state.correct = result.correct;
                state.feedback = result.feedback;
                state.hints = result.hints || [];
                if (result.correct) {
                    localStorage.removeItem(this._exerciseKey(index));
                    if (result.xp_earned) {
                        window._showToast('+' + result.xp_earned + ' XP', 'success');
                        window._refreshNavbar();
                    }
                }
            } catch (e) {
                state.feedback = 'Failed to evaluate. Please try again.';
                state.correct = false;
            } finally {
                state.submitting = false;
            }
        },

        renderLessonContent(content) {
            if (!content.sections) return '';
            let html = '';
            if (content.objective) {
                html += `<div class="bg-brand-50 dark:bg-brand-900/30 border border-brand-200 dark:border-brand-800 rounded-lg p-4 mb-6">
                    <p class="text-sm font-medium text-brand-800 dark:text-brand-300">Learning Objective</p>
                    <p class="text-brand-700 dark:text-brand-200">${content.objective}</p>
                </div>`;
            }
            for (const section of content.sections) {
                html += `<h3 class="text-xl font-semibold mt-6 mb-3">${section.heading}</h3>`;
                html += marked.parse(section.content);
            }
            if (content.summary) {
                html += `<div class="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                    <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Summary</p>
                    <p class="text-gray-700 dark:text-gray-300">${content.summary}</p>
                </div>`;
            }
            return html;
        },

        goToExercise(i) {
            if (i < 0 || i >= this.exercises.length) return;
            this.currentExerciseIndex = i;
            this.$nextTick(() => this.editors[i]?.resize());
        },

        openFeedback() {
            if (this.feedbackSubmitted) return;
            this.feedbackTags = [];
            this.feedbackMessage = '';
            this.feedbackError = null;
            this.feedbackModalOpen = true;
        },

        toggleFeedbackTag(tag) {
            const i = this.feedbackTags.indexOf(tag);
            if (i === -1) this.feedbackTags.push(tag);
            else this.feedbackTags.splice(i, 1);
        },

        async submitFeedback() {
            if (this.feedbackSubmitting) return;
            if (this.feedbackTags.length === 0 && !this.feedbackMessage.trim()) return;
            this.feedbackSubmitting = true;
            this.feedbackError = null;
            try {
                await API.post('/lessons/' + this.lesson.id + '/feedback', {
                    tags: this.feedbackTags,
                    message: this.feedbackMessage.trim(),
                });
                this.feedbackSubmitted = true;
                this.feedbackModalOpen = false;
                window._showToast('Feedback submitted \u2014 thanks!', 'success');
            } catch (e) {
                this.feedbackError = e.message || 'Failed to submit feedback.';
            } finally {
                this.feedbackSubmitting = false;
            }
        },

        async loadAltExplanation() {
            if (this.altExplanationLoading) return;
            if (this.altExplanation) {
                this.altExplanationOpen = !this.altExplanationOpen;
                return;
            }
            this.altExplanationLoading = true;
            this.altExplanationError = null;
            try {
                const data = await API.post('/lessons/' + this.lesson.id + '/explain', {});
                this.altExplanation = marked.parse(data.markdown);
                this.altExplanationOpen = true;
            } catch (e) {
                this.altExplanationError = 'Could not generate alternative explanation.';
            } finally {
                this.altExplanationLoading = false;
            }
        },

        async completeAndQuiz() {
            this.quizLoading = true;
            this.error = null;
            try {
                if (!this.alreadyCompleted) {
                    await API.post('/lessons/' + this.lesson.id + '/complete', {});
                }
                await API.post('/lessons/' + this.lesson.id + '/quiz', {});
                window._navigate('/lessons/' + this.lesson.id + '/quiz');
            } catch (e) {
                this.error = 'Failed to start quiz. Please try again.';
            } finally {
                this.quizLoading = false;
            }
        },
    };
}

function quizView() {
    return {
        questions: [],
        currentIndex: 0,
        answers: {},
        selectedAnswer: null,
        shortAnswer: '',
        answered: false,
        feedback: null,
        showResults: false,
        score: 0,
        correctCount: 0,
        xpEarned: 0,
        newAchievements: [],
        grading: false,
        submitting: false,
        submitted: false,
        skillId: null,
        lessonId: null,
        quizId: null,
        error: null,

        get currentQuestion() {
            return this.questions[this.currentIndex] || {};
        },

        askTutor(index) {
            const q = this.questions[index];
            if (!q || !this.skillId) return;
            const questionText = encodeURIComponent(q.question);
            let url = '/chat/' + this.skillId + '?question=' + questionText;
            if (this.lessonId) url += '&lesson=' + this.lessonId;
            window._navigate(url);
        },

        async loadQuiz() {
            const lessonId = window.location.pathname.match(/\/lessons\/(\d+)/)?.[1];
            if (!lessonId) return;
            this.lessonId = lessonId;
            this.error = null;
            try {
                const data = await API.get('/lessons/' + lessonId + '/quiz');
                if (data.error) throw new Error(data.error);
                this.questions = data.questions || [];
                this.quizId = data.quiz_id;
                this.skillId = data.skill_id;
                this.currentIndex = 0;
                this.answers = {};
                this.showResults = false;
                this.submitted = false;
            } catch (e) {
                this.error = e.message || 'Failed to load quiz.';
            }
        },

        selectOption(option) {
            if (this.answered) return;
            this.selectedAnswer = option;
        },

        checkAnswer() {
            if (!this.selectedAnswer) return;
            const correct = this.selectedAnswer === this.currentQuestion.correct_answer;
            this.answers[this.currentIndex] = { answer: this.selectedAnswer, correct };
            this.feedback = correct
                ? 'Correct! ' + (this.currentQuestion.explanation || '')
                : 'Not quite. ' + (this.currentQuestion.explanation || 'The correct answer is: ' + this.currentQuestion.correct_answer);
            this.answered = true;
        },

        async submitShortAnswer() {
            if (!this.shortAnswer.trim() || this.grading) return;
            this.grading = true;
            try {
                const result = await API.post('/quizzes/grade', {
                    question: this.currentQuestion,
                    answer: this.shortAnswer.trim(),
                });
                this.answers[this.currentIndex] = { answer: this.shortAnswer, correct: result.correct };
                this.feedback = result.feedback;
                this.answered = true;
            } catch (e) {
                this.feedback = 'Failed to grade answer. Please try again.';
            } finally {
                this.grading = false;
            }
        },

        async nextQuestion() {
            if (this.currentIndex < this.questions.length - 1) {
                this.currentIndex++;
                this.selectedAnswer = null;
                this.shortAnswer = '';
                this.answered = false;
                this.feedback = null;
            } else {
                await this.finishQuiz();
            }
        },

        async finishQuiz() {
            if (this.submitted) return; // Prevent double-submit
            this.submitted = true;
            this.submitting = true;
            this.correctCount = Object.values(this.answers).filter(a => a.correct).length;
            this.score = this.correctCount / this.questions.length;
            try {
                const result = await API.post('/quizzes/submit', {
                    quiz_id: this.quizId,
                    answers: this.answers,
                    score: this.score,
                });
                this.xpEarned = result.xp_earned;
                this.newAchievements = result.new_achievements || [];
            } catch (e) {
                this.xpEarned = 0;
            }
            this.showResults = true;
            this.submitting = false;
            window._refreshNavbar();
            if (this.newAchievements.length > 0) {
                setTimeout(() => window._showAchievement(this.newAchievements[0]), 500);
            }
        },
    };
}

function chatView() {
    return {
        messages: [],
        input: '',
        thinking: false,
        skillId: null,
        skillName: '',
        lessonId: null,

        async initChat() {
            const newSkillId = window.location.pathname.match(/\/chat\/(\d+)/)?.[1];
            const params = new URLSearchParams(window.location.search);
            const newLessonId = params.get('lesson') || null;
            const questionParam = params.get('question') || null;

            // Skip if already showing this exact chat
            if (this.skillId === newSkillId && this.lessonId === newLessonId && this.messages.length > 0) return;

            // Reset state for new chat
            this.skillId = newSkillId;
            this.lessonId = newLessonId;
            this.messages = [];
            this.input = '';
            this.thinking = false;
            this.skillName = '';

            if (this.skillId) {
                try {
                    const data = await API.get('/skills/' + this.skillId);
                    this.skillName = data.skill?.name || '';
                    // Only load history for skill-wide chat (no lesson param)
                    if (!this.lessonId) {
                        const history = await API.get('/chat/' + this.skillId + '/history');
                        this.messages = history.messages || [];
                    }
                } catch (e) {
                    console.error(e);
                }
            }
            if (this.messages.length === 0) {
                this.messages.push({
                    role: 'assistant',
                    content: this.skillName
                        ? `Hi! I'm your tutor for **${this.skillName}**. Ask me anything about what you're learning, and I'll help you understand it better.`
                        : `Hi! I'm your AI tutor. What would you like to learn about?`,
                });
            }
            if (questionParam) {
                this.input = 'I got this quiz question wrong and need help understanding it: ' + questionParam;
                this.$nextTick(() => this.send());
            }
        },

        renderMarkdown(text) {
            return marked.parse(text || '');
        },

        async send() {
            if (!this.input.trim() || this.thinking) return;
            const msg = this.input.trim();
            this.input = '';
            this.messages.push({ role: 'user', content: msg });
            this.thinking = true;
            this.$nextTick(() => {
                this.$refs.messages.scrollTop = this.$refs.messages.scrollHeight;
            });
            try {
                const result = await API.post('/chat', {
                    skill_id: this.skillId ? parseInt(this.skillId) : null,
                    lesson_id: this.lessonId ? parseInt(this.lessonId) : null,
                    message: msg,
                    history: this.messages.slice(0, -1).slice(-20),
                });
                this.messages.push({ role: 'assistant', content: result.response });
            } catch (e) {
                this.messages.push({ role: 'assistant', content: 'Sorry, something went wrong. Please try again.' });
            } finally {
                this.thinking = false;
                this.$nextTick(() => {
                    this.$refs.messages.scrollTop = this.$refs.messages.scrollHeight;
                });
            }
        },
    };
}

function reviewView() {
    return {
        cards: [],
        currentIndex: 0,
        revealed: false,
        loading: true,
        completed: false,
        reviewedCount: 0,
        xpEarned: 0,

        get currentCard() {
            return this.cards[this.currentIndex] || null;
        },

        renderMarkdown(text) {
            return marked.parse(text || '');
        },

        async loadReviewQueue() {
            this.loading = true;
            try {
                const data = await API.get('/review/queue');
                this.cards = data.cards || [];
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        async rateCard(quality) {
            try {
                const result = await API.post('/review/' + this.currentCard.id + '/rate', { quality });
                this.xpEarned += result.xp_earned || 0;
                this.reviewedCount++;
                if (result.new_achievements?.length > 0) {
                    setTimeout(() => window._showAchievement(result.new_achievements[0]), 300);
                }
            } catch (e) {
                console.error(e);
            }
            if (this.currentIndex < this.cards.length - 1) {
                this.currentIndex++;
                this.revealed = false;
            } else {
                this.completed = true;
                window._refreshNavbar();
            }
        },
    };
}

function progressView() {
    return {
        stats: null,
        allAchievements: [],
        chartData: null,
        chartsReady: false,
        _charts: {},

        async loadProgress() {
            try {
                const [progress, achievements, charts] = await Promise.all([
                    API.get('/progress'),
                    API.get('/achievements'),
                    API.get('/progress/charts'),
                ]);
                this.stats = progress;
                this.allAchievements = achievements;
                this.chartData = charts;
                this.chartsReady = true;
                this.$nextTick(() => this._renderCharts());
            } catch (e) {
                console.error(e);
            }
        },

        _renderCharts() {
            const isDark = document.documentElement.classList.contains('dark');
            const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
            const textColor = isDark ? '#9ca3af' : '#6b7280';

            // Destroy existing charts before re-rendering (SPA re-navigation)
            for (const key of Object.keys(this._charts)) {
                this._charts[key]?.destroy();
            }
            this._charts = {};

            const scaleBase = {
                ticks: { color: textColor },
                grid: { color: gridColor },
            };

            // Activity Chart (stacked bar)
            const actCtx = document.getElementById('activityChart');
            if (actCtx && this.chartData?.activity) {
                this._charts.activity = new Chart(actCtx, {
                    type: 'bar',
                    data: {
                        labels: this.chartData.activity.labels.map(d => d.slice(5)),
                        datasets: [
                            { label: 'Lessons', data: this.chartData.activity.lessons, backgroundColor: 'rgba(14,165,233,0.7)', stack: 'a' },
                            { label: 'Quizzes', data: this.chartData.activity.quizzes, backgroundColor: 'rgba(168,85,247,0.7)', stack: 'a' },
                        ],
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { labels: { color: textColor } } },
                        scales: {
                            x: { ...scaleBase, ticks: { ...scaleBase.ticks, maxTicksLimit: 10 } },
                            y: { ...scaleBase, beginAtZero: true, ticks: { ...scaleBase.ticks, stepSize: 1 } },
                        },
                    },
                });
            }

            // Quiz Score Trend (line)
            const qCtx = document.getElementById('quizScoreChart');
            if (qCtx && this.chartData?.quiz_scores?.labels?.length) {
                this._charts.quizScore = new Chart(qCtx, {
                    type: 'line',
                    data: {
                        labels: this.chartData.quiz_scores.labels,
                        datasets: [{
                            label: 'Score (%)',
                            data: this.chartData.quiz_scores.scores,
                            borderColor: 'rgba(34,197,94,0.9)',
                            backgroundColor: 'rgba(34,197,94,0.1)',
                            tension: 0.3,
                            fill: true,
                            pointRadius: 4,
                            pointBackgroundColor: 'rgba(34,197,94,1)',
                        }],
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { labels: { color: textColor } } },
                        scales: {
                            x: scaleBase,
                            y: { ...scaleBase, min: 0, max: 100, ticks: { ...scaleBase.ticks, callback: v => v + '%' } },
                        },
                    },
                });
            }

            // Skills Progress (horizontal stacked bar)
            const sCtx = document.getElementById('skillsChart');
            if (sCtx && this.chartData?.skills?.labels?.length) {
                this._charts.skills = new Chart(sCtx, {
                    type: 'bar',
                    data: {
                        labels: this.chartData.skills.labels,
                        datasets: [
                            { label: 'Completed', data: this.chartData.skills.completed, backgroundColor: 'rgba(34,197,94,0.7)', stack: 's' },
                            { label: 'Remaining', data: this.chartData.skills.total.map((t, i) => t - (this.chartData.skills.completed[i] || 0)), backgroundColor: 'rgba(209,213,219,0.5)', stack: 's' },
                        ],
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        plugins: { legend: { labels: { color: textColor } } },
                        scales: {
                            x: { ...scaleBase, stacked: true, beginAtZero: true },
                            y: { ...scaleBase, stacked: true },
                        },
                    },
                });
            }
        },

        exportData() {
            window.open('/api/progress/export', '_blank');
        },
    };
}

// Global helpers for child components
window._navigate = () => {};
window._refresh = () => {};
window._refreshNavbar = () => {};
window._showToast = () => {};

const _origApp = app;
app = function() {
    const instance = _origApp();
    const origInit = instance.init;
    instance.init = async function() {
        window._navigate = (path) => this.navigate(path);
        window._refresh = () => this.refresh();
        window._refreshNavbar = () => this.refreshNavbar();
        window._showToast = (msg, type) => this.showToast(msg, type);
        window._showAchievement = (a) => this.showAchievement(a);
        await origInit.call(this);
    };
    return instance;
};
