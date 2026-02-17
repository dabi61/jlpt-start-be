from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.n5.models import N5Exam, N5Question, N5QuestionItem, N5Section, N5Subcategory


User = get_user_model()


class PracticeAttemptFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='practice@example.com',
            password='StrongPassword123!',
            status=User.Status.ACTIVE,
        )
        self.client.force_authenticate(user=self.user)

        section = N5Section.objects.create(code='nghe', name='Nghe', sort_order=1)
        sub = N5Subcategory.objects.create(section=section, code='traloinhanh', source_key='TraLoiNhanh', name='Trả lời nhanh', sort_order=1)
        self.exam = N5Exam.objects.create(subcategory=sub, slug='exam-1', name='Exam 1', source_file='n5/test.json', jlpt_level=5)

        q = N5Question.objects.create(exam=self.exam, source_id=1, display_order=0, kind='test', title='t', jlpt_level=5)
        self.item1 = N5QuestionItem.objects.create(question=q, item_order=0, question_text='q1', answers=['a', 'b', 'c', 'd'], correct_answer=2)
        self.item2 = N5QuestionItem.objects.create(question=q, item_order=1, question_text='q2', answers=['a', 'b', 'c', 'd'], correct_answer=1)

    def test_create_attempt_resume(self):
        url = '/api/practice/attempts/'
        payload = {'level': 'N5', 'exam_id': self.exam.id, 'resume': True}

        first = self.client.post(url, payload, format='json')
        body1 = first.json()
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        attempt_id = body1['data']['id']
        self.assertEqual(body1['data']['level'], 'N5')
        self.assertEqual(body1['data']['exam_id'], self.exam.id)

        second = self.client.post(url, payload, format='json')
        body2 = second.json()
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(body2['data']['id'], attempt_id)

    def test_answer_and_submit(self):
        create = self.client.post('/api/practice/attempts/', {'level': 'N5', 'exam_id': self.exam.id}, format='json')
        attempt_id = create.json()['data']['id']

        ans_url = f'/api/practice/attempts/{attempt_id}/answers/'
        resp = self.client.post(ans_url, {'question_item_id': self.item1.id, 'selected_answer': 2}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        answers = resp.json()['data']
        self.assertEqual(len(answers), 1)
        self.assertTrue(answers[0]['is_correct'])

        # Wrong answer for item2
        resp2 = self.client.post(ans_url, {'question_item_id': self.item2.id, 'selected_answer': 4}, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)

        submit_url = f'/api/practice/attempts/{attempt_id}/submit/'
        submitted = self.client.post(submit_url, {}, format='json')
        body = submitted.json()['data']
        self.assertEqual(submitted.status_code, status.HTTP_200_OK)
        self.assertEqual(body['status'], 'SUBMITTED')
        self.assertEqual(body['total_items'], 2)
        self.assertEqual(body['answered_items'], 2)
        self.assertEqual(body['correct_items'], 1)

