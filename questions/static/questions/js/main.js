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
            return '/question/' + questionId + '/like/';
        },
        answer_like: function(questionId, answerId) {
            return '/question/' + questionId + '/answer/' + answerId + '/like/';
        },
        mark_correct: function(questionId, answerId) {
            return '/question/' + questionId + '/answer/' + answerId + '/mark-correct/';
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

    document.querySelectorAll('.vote-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (this.disabled) {
                window.location.href = '/login/?next=' + window.location.pathname;
                return;
            }
            
            const id = this.dataset.id;
            const type = this.dataset.type;
            const currentVote = parseInt(this.dataset.userVote || '0', 10);
            const clickedValue = this.dataset.action === 'like' ? 1 : -1;
            
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
                    ratingEl.textContent = data.rating;
                    
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
        });
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
});