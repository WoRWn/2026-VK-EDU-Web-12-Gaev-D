document.addEventListener('DOMContentLoaded', function() {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    const API_URLS = {
        question_like: function(questionId) {
            return `/question/${questionId}/like/`;
        },
        answer_like: function(questionId, answerId) {
            return `/question/${questionId}/answer/${answerId}/like/`;
        },
        mark_correct: function(questionId, answerId) {
            return `/question/${questionId}/answer/${answerId}/mark-correct/`;
        }
    };

    function applyVoteState(btn, vote) {
        const parent = btn.closest('.vote-column');
        if (!parent) return;
        const upBtn = parent.querySelector('[data-action="like"]');
        const downBtn = parent.querySelector('[data-action="dislike"]');
        if (!upBtn || !downBtn) return;

        upBtn.classList.remove('text-success', 'text-danger', 'text-primary', 'fw-bold');
        downBtn.classList.remove('text-danger', 'text-success', 'text-primary', 'fw-bold');

        if (vote === 1) {
            upBtn.classList.add('text-success', 'fw-bold');
        } else if (vote === -1) {
            downBtn.classList.add('text-danger', 'fw-bold');
        } else {
            upBtn.classList.add('text-primary');
            downBtn.classList.add('text-primary');
        }
    }

    function initializeVoteButtons() {
        document.querySelectorAll('.vote-btn').forEach(function(btn) {
            const vote = parseInt(btn.dataset.userVote || '0', 10);
            applyVoteState(btn, vote);
        });
    }

    function handleVoteClick(btn) {
        if (btn.disabled) {
            window.location.href = '/login/?next=' + window.location.pathname;
            return;
        }
        
        const id = btn.dataset.id;
        const type = btn.dataset.type;
        const currentVote = parseInt(btn.dataset.userVote || '0', 10);
        const clickedValue = btn.dataset.action === 'like' ? 1 : -1;
        
        let targetVote = clickedValue;
        if (currentVote === clickedValue) {
            targetVote = 0;
        }

        const ratingEl = document.getElementById(
            (type === 'question' ? 'q-rating-' : 'a-rating-') + id
        );
        
        let url;
        let paramKey;
        
        if (type === 'question') {
            url = API_URLS.question_like(id);
            paramKey = 'question_id';
        } else {
            const questionCard = btn.closest('.card');
            const questionId = questionCard ? questionCard.querySelector('[data-qid]')?.dataset.qid : null;
            if (!questionId) {
                console.error('Could not find question_id for answer vote');
                return;
            }
            url = API_URLS.answer_like(questionId, id);
            paramKey = 'answer_id';
        }

        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ [paramKey]: id, vote: targetVote })
        })
        .then(function(response) {
            if (response.status === 403) throw new Error('Auth required');
            if (!response.ok) throw new Error('Network error');
            return response.json();
        })
        .then(function(data) {
            if (data.status === 'ok') {
                if (ratingEl) ratingEl.textContent = data.rating;
                
                const parent = btn.closest('.vote-column');
                parent.querySelectorAll('.vote-btn').forEach(b => {
                    b.dataset.userVote = data.user_vote;
                });

                applyVoteState(btn, data.user_vote);
            }
        })
        .catch(function(err) {
            if (err.message !== 'Auth required') alert('Ошибка при отправке голоса.');
        });
    }

    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.vote-btn');
        if (btn) {
            e.preventDefault();
            handleVoteClick(btn);
        }
    });

    document.querySelectorAll('.correct-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (this.disabled) {
                window.location.href = '/login/?next=' + window.location.pathname;
                return;
            }
            
            const isCurrentlyApproved = this.dataset.approved == "true";
            const shouldBeApproved = !isCurrentlyApproved;
            const answerCard = this.closest(".card");
            const questionId = this.dataset.qid;
            const answerId = this.dataset.aid;

            fetch(API_URLS.mark_correct(questionId, answerId), {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ question_id: questionId, answer_id: answerId, is_approved: shouldBeApproved.toString() })
            })
            .then(function(response) {
                if (response.status === 403) throw new Error('Auth required');
                if (!response.ok) throw new Error('Network error');
                return response.json();
            })
            .then(function(data) {
                if (data.status === 'ok') {
                    btn.dataset.approved = data.is_approved.toString();
                    if (data.is_approved) {
                        answerCard.classList.add('border-start', 'border-4', 'border-success');
                        btn.classList.remove('text-secondary');
                        btn.classList.add('text-success');
                    } else {
                        answerCard.classList.remove('border-start', 'border-4', 'border-success');
                        btn.classList.remove('text-success');
                        btn.classList.add('text-secondary');
                    }
                }
            })
            .catch(function(err) {
                if (err.message !== 'Auth required') alert('Не удалось обновить статус ответа.');
            });
        });
    });

    initializeVoteButtons();

if (typeof Centrifuge !== 'undefined' && window.questionId && window.centrifugoToken) {
    const centrifuge = new Centrifuge('ws://localhost:8001/connection/websocket', {
        token: window.centrifugoToken
    });

    centrifuge.connect();

    const channelName = `question_${window.questionId}`;
    const subscription = centrifuge.newSubscription(channelName);

    subscription.on('publication', function(ctx) {
        handleNewAnswer(ctx.data);
    });

    subscription.subscribe();

    function handleNewAnswer(data) {
        if (document.getElementById(`answer-${data.answer_id}`)) {
            return;
        }

        const answersList = document.getElementById('answers-list');
        const noAnswersMsg = document.getElementById('no-answers-msg');
        const currentPage = parseInt(window.currentPage, 10) || 1;

        if (noAnswersMsg) {
            noAnswersMsg.remove();
            insertAnswerToDOM(data, answersList);
            updateAnswersCounter(1);
            return;
        }

        if (currentPage === 1) {
            insertAnswerToDOM(data, answersList);
            updateAnswersCounter();
            
            const newEl = document.getElementById(`answer-${data.answer_id}`);
            if (newEl) {
                newEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                newEl.style.transition = 'background 0.8s';
                newEl.style.background = '#e8f5e9';
                setTimeout(() => { newEl.style.background = ''; }, 1500);
            }
            return;
        }

        alert(`Появился новый ответ на вопрос!`);
    }

    function insertAnswerToDOM(data, container) {
        const canApprove = window.currentUserId && window.currentUserId === window.questionAuthorId;
    
        const approveButton = canApprove ? `
            <button class="btn btn-sm btn-link p-0 correct-btn mt-2 fs-4 text-secondary"
                    data-qid="${window.questionId}"
                    data-aid="${data.answer_id}"
                    data-approved="false"
                    title="Отметить как правильный">
                ✓
            </button>
        ` : '';

        const html = `
            <div id="answer-${data.answer_id}" class="card shadow-sm mb-3">
                <div class="card-body p-4">
                    <div class="d-flex gap-3">
                        <div class="vote-column d-flex flex-column align-items-center" style="min-width: 60px;">
                            <img src="/static/img/person.svg" class="rounded-circle border" width="40" height="40" alt="Author">
                            <span class="d-inline-block">
                                <button class="btn btn-sm btn-link p-0 vote-btn text-primary" 
                                        data-id="${data.answer_id}" data-type="answer" data-action="like" data-user-vote="0">▲</button>
                            </span>
                            <div class="fw-bold my-1 text-dark fs-5" id="a-rating-${data.answer_id}">0</div>
                            <span class="d-inline-block">
                                <button class="btn btn-sm btn-link p-0 vote-btn text-primary" 
                                        data-id="${data.answer_id}" data-type="answer" data-action="dislike" data-user-vote="0">▼</button>
                            </span>
                            ${approveButton}
                        </div>
                        <div class="flex-grow-1 d-flex flex-column">
                            <div class="text-secondary mb-3 lh-lg">${data.text.replace(/\n/g, '<br>')}</div>
                            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 pt-2 border-top mt-auto">
                                <div class="d-flex align-items-center gap-2">
                                    <a href="#" class="text-decoration-none text-secondary fw-bold small">Автор ответа: ${data.author_username}</a>
                                </div>
                                <div class="text-muted small">отвечен только что</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('afterbegin', html);
    }

    function updateAnswersCounter(increment = 1) {
        const countEl = document.querySelector('h2.h5.mb-0.text-secondary span.fw-bold.text-dark.fs-4');
        if (countEl) {
            const current = parseInt(countEl.textContent, 10) || 0;
            countEl.textContent = current + increment;
        }
    }
}});

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const suggestionsBox = document.getElementById('search-suggestions');
    let debounceTimer;

    if (searchInput && suggestionsBox) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            clearTimeout(debounceTimer);

            if (query.length < 2) {
                suggestionsBox.style.display = 'none';
                return;
            }

            debounceTimer = setTimeout(() => {
                fetch(`/api/search/?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        suggestionsBox.innerHTML = ''; 
                        
                        if (data.length === 0) {
                            suggestionsBox.innerHTML = '<div class="list-group-item text-muted small">Ничего не найдено</div>';
                        } else {
                            data.forEach(item => {
                                const link = document.createElement('a');
                                link.href = item.url;
                                link.className = 'list-group-item list-group-item-action';
                                link.innerHTML = item.title;
                                suggestionsBox.appendChild(link);
                            });
                        }
                        suggestionsBox.style.display = 'block';
                    })
                    .catch(err => console.error('Search error:', err));
            }, 500);
        });

        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
                suggestionsBox.style.display = 'none';
            }
        });
    }
});