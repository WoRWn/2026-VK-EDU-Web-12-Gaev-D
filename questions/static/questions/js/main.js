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
        question_like: '/question/like/',
        answer_like: '/answer/like/',
        mark_correct: '/answer/mark-correct/'
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

    document.querySelectorAll('.vote-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (this.disabled) {
                window.location.href = '/login/?next=' + window.location.pathname;
                return;
            }
            const id = this.dataset.id;
            const type = this.dataset.type;
            const action = this.dataset.action;
            const ratingEl = document.getElementById(
                (type === 'question' ? 'q-rating-' : 'a-rating-') + id
            );
            const url = (type === 'question') ? API_URLS.question_like : API_URLS.answer_like;

            fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ [type + '_id']: id, action: action })
            })
            .then(function(response) {
                if (response.status === 403) throw new Error('Auth required');
                if (!response.ok) throw new Error('Network error');
                return response.json();
            })
            .then(function(data) {
                if (data.status === 'ok') {
                    ratingEl.textContent = data.rating;
                    applyVoteState(btn, data.user_vote);
                }
            })
            .catch(function(err) {
                if (err.message !== 'Auth required') alert('Ошибка при отправке голоса.');
            });
        });
    });

    document.querySelectorAll('.correct-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (this.disabled) {
                window.location.href = '/login/?next=' + window.location.pathname;
                return;
            }
            fetch(API_URLS.mark_correct, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ question_id: this.dataset.qid, answer_id: this.dataset.aid })
            })
            .then(function(response) {
                if (response.status === 403) throw new Error('Auth required');
                if (!response.ok) throw new Error('Network error');
                return response.json();
            })
            .then(function(data) {
                if (data.status === 'ok') {
                    const answerCard = btn.closest('.card');
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
});