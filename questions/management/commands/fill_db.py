import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from faker import Faker
from questions.models import Profile, Tag, Question, Answer, QuestionLike, AnswerLike

fake = Faker("ru_RU")
BATCH_SIZE = 1000

TEST_PASSWORD_HASH = make_password("123456")

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("ratio", type=int)

    def bulk_create_batch(self, model, objects):
        for i in range(0, len(objects), BATCH_SIZE):
            model.objects.bulk_create(objects[i : i + BATCH_SIZE], ignore_conflicts=True)

    def handle(self, *args, **options):
        ratio = options["ratio"]
        self.stdout.write(f"Starting generation with ratio={ratio}")

        user_ids = self.create_users(ratio)
        self.create_profiles(user_ids)
        tag_ids = self.create_tags(ratio)
        question_ids = self.create_questions(ratio * 10, user_ids)
        self.create_question_tags(ratio * 10, question_ids, tag_ids)
        answer_ids = self.create_answers(ratio * 100, question_ids, user_ids)
        
        total_likes = ratio * 200
        self.create_question_likes(total_likes // 2, user_ids, question_ids)
        self.create_answer_likes(total_likes // 2, user_ids, answer_ids)

        self.stdout.write(self.style.SUCCESS("Generation complete."))

    def create_users(self, count):
        self.stdout.write(f"Creating {count} users...")
        users = [
            User(
                username=fake.user_name(), 
                email=fake.email(), 
                password=TEST_PASSWORD_HASH
            ) for _ in range(count)
        ]
        self.bulk_create_batch(User, users)
        ids = list(User.objects.values_list("id", flat=True).order_by("id")[:count])
        self.stdout.write(f"Created {len(ids)} users.")
        return ids

    def create_profiles(self, user_ids):
        self.stdout.write(f"Creating {len(user_ids)} profiles...")
        profiles = [Profile(user_id=uid, nickname=fake.name()) for uid in user_ids]
        self.bulk_create_batch(Profile, profiles)
        self.stdout.write(f"Created {len(profiles)} profiles.")

    def create_tags(self, count):
        self.stdout.write(f"Creating {count} tags...")
        tags = [
            Tag(
                name=f"{fake.word().capitalize()}_{i}", 
                color="#{:06x}".format(random.randint(0, 0xFFFFFF))
            ) for i in range(count)
        ]
        self.bulk_create_batch(Tag, tags)
        ids = list(Tag.objects.values_list("id", flat=True).order_by("id")[:count])
        self.stdout.write(f"Created {len(ids)} tags.")
        return ids

    def create_questions(self, count, user_ids):
        self.stdout.write(f"Creating {count} questions...")
        authors = random.choices(user_ids, k=count)
        questions = []
        for i in range(count):
            questions.append(
                Question(
                    title=fake.sentence(nb_words=5),
                    text=fake.text(max_nb_chars=500),
                    author_id=authors[i],
                    created_at=fake.date_time_between(start_date="-2y", end_date="now")
                )
            )
            if len(questions) >= BATCH_SIZE:
                self.bulk_create_batch(Question, questions)
                questions = []
        if questions:
            self.bulk_create_batch(Question, questions)
        ids = list(Question.objects.values_list("id", flat=True).order_by("id")[:count])
        self.stdout.write(f"Created {len(ids)} questions.")
        return ids

    def create_question_tags(self, count, question_ids, tag_ids):
        self.stdout.write(f"Creating {count} question-tag links...")
        q_ids = random.choices(question_ids, k=count)
        t_ids = random.choices(tag_ids, k=count)
        links = [Question.tags.through(question_id=q, tag_id=t) for q, t in zip(q_ids, t_ids)]
        self.bulk_create_batch(Question.tags.through, links)
        self.stdout.write(f"Created {len(links)} links.")

    def create_answers(self, count, question_ids, user_ids):
        self.stdout.write(f"Creating {count} answers...")
        q_ids = random.choices(question_ids, k=count)
        u_ids = random.choices(user_ids, k=count)
        answers = []
        for i in range(count):
            answers.append(
                Answer(
                    question_id=q_ids[i],
                    author_id=u_ids[i],
                    text=fake.text(max_nb_chars=300),
                    created_at=fake.date_time_between(start_date="-1y", end_date="now")
                )
            )
            if len(answers) >= BATCH_SIZE:
                self.bulk_create_batch(Answer, answers)
                answers = []
        if answers:
            self.bulk_create_batch(Answer, answers)
        ids = list(Answer.objects.values_list("id", flat=True).order_by("id")[:count])
        self.stdout.write(f"Created {len(ids)} answers.")
        return ids

    def create_question_likes(self, count, user_ids, question_ids):
        self.stdout.write(f"Creating {count} question likes...")
        u_ids = random.choices(user_ids, k=count)
        q_ids = random.choices(question_ids, k=count)
        likes = [QuestionLike(user_id=u, question_id=q, created_at=fake.date_time()) for u, q in zip(u_ids, q_ids)]
        self.bulk_create_batch(QuestionLike, likes)
        self.stdout.write(f"Created {len(likes)} question likes.")

    def create_answer_likes(self, count, user_ids, answer_ids):
        self.stdout.write(f"Creating {count} answer likes...")
        u_ids = random.choices(user_ids, k=count)
        a_ids = random.choices(answer_ids, k=count)
        likes = [AnswerLike(user_id=u, answer_id=a, created_at=fake.date_time()) for u, a in zip(u_ids, a_ids)]
        self.bulk_create_batch(AnswerLike, likes)
        self.stdout.write(f"Created {len(likes)} answer likes.")