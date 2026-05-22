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
        """Создает объекты пачками и возвращает список всех созданных объектов с ID"""
        all_created = []
        for i in range(0, len(objects), BATCH_SIZE):
            batch = objects[i : i + BATCH_SIZE]
            created = model.objects.bulk_create(batch)
            all_created.extend(created)
        return all_created

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
        # ✅ Берем ID прямо из результата bulk_create
        created_users = User.objects.bulk_create(users)
        ids = [u.id for u in created_users]
        self.stdout.write(f"Created {len(ids)} users.")
        return ids

    def create_profiles(self, user_ids):
        self.stdout.write(f"Creating {len(user_ids)} profiles...")
        profiles = [Profile(user_id=uid, nickname=fake.name()) for uid in user_ids]
        Profile.objects.bulk_create(profiles)
        self.stdout.write(f"Created {len(profiles)} profiles.")

    def create_tags(self, count):
        self.stdout.write(f"Creating {count} tags...")
        tags = [
            Tag(
                name=f"{fake.word().capitalize()}_{i}", 
                color="#{:06x}".format(random.randint(0, 0xFFFFFF))
            ) for i in range(count)
        ]
        # ✅ Берем ID прямо из результата bulk_create
        created_tags = Tag.objects.bulk_create(tags)
        ids = [t.id for t in created_tags]
        self.stdout.write(f"Created {len(ids)} tags.")
        return ids

    def create_questions(self, count, user_ids):
        self.stdout.write(f"Creating {count} questions...")
        authors = random.choices(user_ids, k=count)
        questions = []
        all_ids = []
        
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
                # ✅ Собираем ID из каждого батча
                created = Question.objects.bulk_create(questions)
                all_ids.extend([q.id for q in created])
                questions = []
        
        if questions:
            created = Question.objects.bulk_create(questions)
            all_ids.extend([q.id for q in created])
            
        self.stdout.write(f"Created {len(all_ids)} questions.")
        return all_ids

    def create_question_tags(self, count, question_ids, tag_ids):
        self.stdout.write(f"Creating {count} question-tag links...")
        pairs = set()
        while len(pairs) < count:
            pairs.add((random.choice(question_ids), random.choice(tag_ids)))
        
        links = [Question.tags.through(question_id=q, tag_id=t) for q, t in pairs]
        self.bulk_create_batch(Question.tags.through, links)
        self.stdout.write(f"Created {len(links)} links.")

    def create_answers(self, count, question_ids, user_ids):
        self.stdout.write(f"Creating {count} answers...")
        q_ids = random.choices(question_ids, k=count)
        u_ids = random.choices(user_ids, k=count)
        answers = []
        all_ids = []
        
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
                # ✅ Собираем ID из каждого батча
                created = Answer.objects.bulk_create(answers)
                all_ids.extend([a.id for a in created])
                answers = []
                
        if answers:
            created = Answer.objects.bulk_create(answers)
            all_ids.extend([a.id for a in created])
            
        self.stdout.write(f"Created {len(all_ids)} answers.")
        return all_ids

    def create_question_likes(self, count, user_ids, question_ids):
        self.stdout.write(f"Creating {count} question likes...")
        pairs = set()
        batch = []
        
        while len(pairs) < count:
            pair = (random.choice(user_ids), random.choice(question_ids))
            if pair not in pairs:
                pairs.add(pair)
                u, q = pair
                batch.append(QuestionLike(user_id=u, question_id=q, value=random.choice([1, -1])))
                
                if len(batch) >= BATCH_SIZE:
                    QuestionLike.objects.bulk_create(batch)
                    batch = []
        
        if batch:
            QuestionLike.objects.bulk_create(batch)
            
        self.stdout.write(f"Created {len(pairs)} question likes.")

    def create_answer_likes(self, count, user_ids, answer_ids):
        self.stdout.write(f"Creating {count} answer likes...")
        pairs = set()
        batch = []
        
        while len(pairs) < count:
            pair = (random.choice(user_ids), random.choice(answer_ids))
            if pair not in pairs:
                pairs.add(pair)
                u, a = pair
                batch.append(AnswerLike(user_id=u, answer_id=a, value=random.choice([1, -1])))
                
                if len(batch) >= BATCH_SIZE:
                    AnswerLike.objects.bulk_create(batch)
                    batch = []
        
        if batch:
            AnswerLike.objects.bulk_create(batch)
            
        self.stdout.write(f"Created {len(pairs)} answer likes.")