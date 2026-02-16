function app() {
    return {
        route: window.location.pathname,
        skills: [],
        progress: null,
        reviewCount: 0,

        async init() {
            window.addEventListener('popstate', () => {
                this.route = window.location.pathname;
            });
            await this.refresh();
        },

        navigate(path) {
            window.history.pushState({}, '', path);
            this.route = path;
            this.refresh();
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
                console.error('Failed to refresh:', e);
            }
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
                this.error = e.message;
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
                this.error = e.message;
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

        async loadSkill() {
            const id = this.$root.__x_route?.match(/\/skills\/(\d+)/)?.[1]
                || window.location.pathname.match(/\/skills\/(\d+)/)?.[1];
            if (!id) return;
            try {
                const data = await API.get('/skills/' + id);
                this.skill = data.skill;
                this.lessons = data.lessons || [];
                this.completedCount = this.lessons.filter(l => l.status === 'completed').length;
            } catch (e) {
                console.error('Failed to load skill:', e);
            }
        },

        async startLesson(lesson, index) {
            if (lesson.content_json) {
                window._navigate('/lessons/' + lesson.id);
                return;
            }
            this.loadingLesson = true;
            try {
                const generated = await API.post('/lessons/generate', {
                    skill_id: this.skill.id,
                    lesson_id: lesson.id,
                });
                window._navigate('/lessons/' + generated.id);
            } catch (e) {
                console.error('Failed to generate lesson:', e);
            } finally {
                this.loadingLesson = false;
            }
        },
    };
}

function lessonView() {
    return {
        lesson: null,
        content: null,
        renderedContent: '',
        loading: true,
        quizLoading: false,

        async loadLesson() {
            const id = window.location.pathname.match(/\/lessons\/(\d+)/)?.[1];
            if (!id) return;
            this.loading = true;
            try {
                this.lesson = await API.get('/lessons/' + id);
                this.content = JSON.parse(this.lesson.content_json || '{}');
                this.renderedContent = this.renderLessonContent(this.content);
            } catch (e) {
                console.error('Failed to load lesson:', e);
            } finally {
                this.loading = false;
            }
        },

        renderLessonContent(content) {
            if (!content.sections) return '';
            let html = '';
            if (content.objective) {
                html += `<div class="bg-brand-50 border border-brand-200 rounded-lg p-4 mb-6">
                    <p class="text-sm font-medium text-brand-800">Learning Objective</p>
                    <p class="text-brand-700">${content.objective}</p>
                </div>`;
            }
            for (const section of content.sections) {
                html += `<h3 class="text-xl font-semibold mt-6 mb-3">${section.heading}</h3>`;
                html += marked.parse(section.content);
            }
            if (content.summary) {
                html += `<div class="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p class="text-sm font-medium text-gray-600 mb-1">Summary</p>
                    <p class="text-gray-700">${content.summary}</p>
                </div>`;
            }
            return html;
        },

        async completeAndQuiz() {
            this.quizLoading = true;
            try {
                await API.post('/lessons/' + this.lesson.id + '/complete', {});
                const quiz = await API.post('/lessons/' + this.lesson.id + '/quiz', {});
                window._navigate('/lessons/' + this.lesson.id + '/quiz');
            } catch (e) {
                console.error('Failed to start quiz:', e);
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
        skillId: null,
        quizId: null,

        get currentQuestion() {
            return this.questions[this.currentIndex] || {};
        },

        async loadQuiz() {
            const lessonId = window.location.pathname.match(/\/lessons\/(\d+)/)?.[1];
            if (!lessonId) return;
            try {
                const data = await API.get('/lessons/' + lessonId + '/quiz');
                this.questions = data.questions || [];
                this.quizId = data.quiz_id;
                this.skillId = data.skill_id;
                this.currentIndex = 0;
                this.answers = {};
                this.showResults = false;
            } catch (e) {
                console.error('Failed to load quiz:', e);
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
            // Refresh global state
            window._refresh();
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

        async initChat() {
            this.skillId = window.location.pathname.match(/\/chat\/(\d+)/)?.[1];
            if (this.skillId) {
                try {
                    const data = await API.get('/skills/' + this.skillId);
                    this.skillName = data.skill?.name || '';
                    // Load previous messages
                    const history = await API.get('/chat/' + this.skillId + '/history');
                    this.messages = history.messages || [];
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
                    message: msg,
                    history: this.messages.slice(0, -1).slice(-20), // last 20 messages for context
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
            } catch (e) {
                console.error(e);
            }
            if (this.currentIndex < this.cards.length - 1) {
                this.currentIndex++;
                this.revealed = false;
            } else {
                this.completed = true;
                if (this.$root && typeof this.$root.__x_refresh === 'function') {
                    this.$root.__x_refresh();
                }
            }
        },
    };
}

function progressView() {
    return {
        stats: null,
        allAchievements: [],

        async loadProgress() {
            try {
                const [progress, achievements] = await Promise.all([
                    API.get('/progress'),
                    API.get('/achievements'),
                ]);
                this.stats = progress;
                this.allAchievements = achievements;
            } catch (e) {
                console.error(e);
            }
        },
    };
}

// Global navigation helper — child components call window._navigate(path)
window._navigate = () => {};
window._refresh = () => {};

const _origApp = app;
app = function() {
    const instance = _origApp();
    const origInit = instance.init;
    instance.init = async function() {
        window._navigate = (path) => this.navigate(path);
        window._refresh = () => this.refresh();
        await origInit.call(this);
    };
    return instance;
};
