from django.http import response
from ..models import Category, Entry, Tag
from ..views import EntryListView, DraftListView
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group


class EntryListViewTest(TestCase):
    """Тесты для главной страницы"""
    def setUp(self):        
        self.category = Category.objects.create(name='Test cat')
        self.user = User.objects.create_user('test', password='pass')
        self.admin_group, _ = Group.objects.get_or_create(name='Administrator')
        self.client.login(username='test', password='pass')
        self.django_entry = Entry.objects.create(
            author=self.user,
            title='Django entry',
            content='text',
            category=self.category)
        self.python_entry = Entry.objects.create(
            author=self.user,
            title='Python entry',
            content='text',
            category=self.category)
        
        self.response = self.client.get(reverse('journal:entry_list'))

    def test_entry_list_view_status(self):
        """Проверяем что главная страница доступна"""
        self.assertEqual(self.response.status_code, 200)

    def test_entry_list_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/entry_list.html')

    def test_entry_list_view_context(self):
        """Проверяем что доступен нужный контекст"""
        self.assertIn('entries', self.response.context)
        self.assertIn('total_entries', self.response.context)
        self.assertIn('categories', self.response.context)
        self.assertIn('tags', self.response.context)

    def test_entry_list_view_filtration(self):
        """Проверяем фильтрацию в EntryListView"""
        response = self.client.get(reverse('journal:entry_list') + '?q=django')
        entries = response.context['entries']
        self.assertIn(self.django_entry, entries)
        self.assertNotIn(self.python_entry, entries)

    def test_entry_list_view_pagination(self):
        """Проверяем корректность paginate_by"""
        page_size = EntryListView.paginate_by

        for i in range(page_size + 1):
            Entry.objects.create(
                title=f'Entry {i}',
                content='text',
                category=self.category
            )

        response = self.client.get(reverse('journal:entry_list'))

        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['entries']), page_size)

    def test_admin_sees_hiden_links(self):
        """Проверяем что администраторам видны кнопки История и Статистика"""
        self.user.groups.add(self.admin_group)
        response = self.client.get(reverse('journal:entry_list'))
        self.assertContains(response, 'Главная')
        self.assertContains(response, 'История')
        self.assertContains(response, 'Статистика')

    def test_not_admin_cant_see_hiden_links(self):
        """Проверяем что обычный пользователь не видит кнопки История и Статистика"""
        response = self.client.get(reverse('journal:entry_list'))
        self.assertContains(response, 'Главная')
        self.assertNotContains(response, 'История')
        self.assertNotContains(response, 'Статистика')
        self.assertNotContains(response, 'Админка')


class EntryDetailViewTest(TestCase):
    """Тесты для страницы просмотра конкретной записи"""
    def setUp(self):
        self.category = Category.objects.create(name='Test cat')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.entry = Entry.objects.create(
            author=self.user,
            title='Test entry',
            content='text',
            category=self.category)
        self.response = self.client.get(reverse('journal:entry_detail', kwargs={'pk': self.entry.pk}))

    def test_entry_deatil_view_status(self):
        """Проверяем что страница конкретной записи доступна"""
        self.assertEqual(self.response.status_code, 200)

    def test_entry_deatil_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/entry_detail.html')

    def test_entry_detail_view_context(self):
        """Проверяем что доступен нужный контекст"""
        self.assertIn('comments', self.response.context)
        self.assertIn('form', self.response.context)

    def test_entry_detail_view_post_method(self):
        """Проверяем что метод post отработал корректно"""
        response = self.client.post(reverse('journal:entry_detail', kwargs={'pk':self.entry.pk}), {
            'content': 'test_entry_detail_view_post_method'
        })
        
        self.assertRedirects(response, reverse('journal:entry_detail', kwargs={'pk': self.entry.pk}))
        comment = self.entry.comments.first()
        self.assertEqual(comment.content, 'test_entry_detail_view_post_method')
        self.assertEqual(self.entry.comments.count(), 1)

    def test_anonim_entry_detail_view_post_method(self):
        """Проверяем оставление анонимного комментарий"""
        self.client.logout()
        
        response = self.client.post(reverse('journal:entry_detail', kwargs={'pk':self.entry.pk}), {
            'content': 'test_anonim_entry_detail_view_post_method'
        })
        
        self.assertRedirects(response, reverse('journal:entry_detail', kwargs={'pk': self.entry.pk}))
        comment = self.entry.comments.first()
        self.assertEqual(comment.content, 'test_anonim_entry_detail_view_post_method')
        self.assertEqual(self.entry.comments.count(), 1)
        self.assertIsNone(comment.author_name)


class EntryCreateViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test cat')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.response = self.client.get(reverse('journal:entry_create'))

    def test_entry_create_view_status(self):
        """Проверяем что форма создания записи доступна"""
        self.assertEqual(self.response.status_code, 200)

    def test_entry_create_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/entry_form.html')

    def test_entry_create_view_post_method(self):
        """Проверяем что метод post отработал корректно"""
        response = self.client.post(reverse('journal:entry_create'), {
            'title': 'test_entry_create_view_post_method',
            'content': 'Content',
            'category': self.category.id
        })
        
        entry = Entry.objects.get(title='test_entry_create_view_post_method')

        self.assertRedirects(response, reverse('journal:entry_detail', kwargs={'pk': entry.pk}))
        self.assertEqual(entry.title, 'test_entry_create_view_post_method')
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(entry.author, self.user)

    def test_anonim_entry_create_view(self):
        """Проверяем что аноним не может зайти на страницу создания записи и его редиректит на /login/"""
        self.client.logout()

        response = self.client.get(reverse('journal:entry_create'))
        self.assertRedirects(response, '/accounts/login/?next=/entry/create/')

    def test_anonim_entry_create_view_post_method(self):
        """Проверяем что аноним не может создать запись и его редиректит на /login/"""
        self.client.logout()

        response = self.client.post(reverse('journal:entry_create'), {
            'title': 'test_anonim_entry_create_view',
            'content': 'Content',
            'category': self.category.id
        })
        self.assertRedirects(response, '/accounts/login/?next=/entry/create/')
        entries = Entry.objects.filter(title='test_anonim_entry_create_view')
        self.assertEqual(entries.count(), 0)


class EntryUpdateViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test cat')
        self.tag = Tag.objects.create(name='test tag')
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.entry = Entry.objects.create(
            author=self.user,
            title='Test entry',
            content='text',
            category=self.category
        )
        self.response = self.client.get(reverse('journal:entry_update', kwargs={'pk': self.entry.pk}))

    def test_entry_update_view_status(self):
        """Проверяем что форма редактирования записи доступна"""        
        self.assertEqual(self.response.status_code, 200)

    def test_published_entry_update_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/entry_form.html')

    def test_entry_update_view_post_method(self):
        """Проверяем что метод post отработал корректно"""
        new_title = 'Новый title'
        response = self.client.post(reverse('journal:entry_update', kwargs={'pk': self.entry.pk}), {
            'title': new_title,
            'content': self.entry.content,
            'category': self.category.id
        })
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, new_title)
        self.assertRedirects(response, reverse('journal:entry_detail', kwargs={'pk': self.entry.pk}))

    def test_entry_update_another_user(self):
        """Проверяем что другой пользователь не может редактировать чужие записи"""
        new_title = 'test_entry_update_another_user'
        User.objects.create_user('another_user', password='pass')
        self.client.login(username='another_user', password='pass')
        response = self.client.post(reverse('journal:entry_update', kwargs={'pk': self.entry.pk}), {
            'title': new_title,
            'content': self.entry.content,
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 403)
        entries = Entry.objects.filter(title=new_title)
        self.assertEqual(entries.count(), 0)

    def test_entry_update_anonim_user(self):
        """Проверяем что не авторизованный пользователь не может редактировать чужие записи"""
        self.client.logout()

        new_title = 'test_entry_update_anonim_user'
        response = self.client.post(reverse('journal:entry_update', kwargs={'pk': self.entry.pk}), {
            'title': new_title,
            'content': self.entry.content,
            'category': self.category.id
        })
        self.assertRedirects(response, f'/accounts/login/?next=/entry/{self.entry.pk}/edit/')
        entries = Entry.objects.filter(title=new_title)
        self.assertEqual(entries.count(), 0) 

    def test_entry_update_admin_permission_user(self):
        """Проверяем что Администратор может редактировать любую запись"""
        admin_group, _ = Group.objects.get_or_create(name='Administrator')
        admin_user = User.objects.create_user('admin_user', password='pass')
        admin_user.groups.add(admin_group)
        self.client.login(username='admin_user', password='pass')

        new_title = 'test_entry_update_admin_permission_user'
        response = self.client.post(reverse('journal:entry_update', kwargs={'pk': self.entry.pk}), {
            'title': new_title,
            'content': self.entry.content,
            'category': self.category.id
        })
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, new_title)
        self.assertRedirects(response, reverse('journal:entry_detail', kwargs={'pk': self.entry.pk}))


class DraftListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', password='pass')
        self.client.login(username='test', password='pass')
        self.category = Category.objects.create(name='Test category')
        self.response = self.client.get(reverse('journal:drafts'))

    def test_draft_list_view_status(self):
        """Проверяем что страница с черновиками доступна"""        
        self.assertEqual(self.response.status_code, 200)

    def test_unpublished_entry_update_view_template(self):
        """Проверяем что используется правильный шаблон"""
        self.assertTemplateUsed(self.response, 'journal/draft_list.html')

    def test_entry_list_view_context(self):
        """Проверяем что доступен нужный контекст"""
        self.assertIn('total_drafts', self.response.context)

    def test_draft_list_view_filtration(self):
        """Проверяем что в DraftListView попадают только не опубликованные записи"""
        
        public_entry = Entry.objects.create(
            author=self.user,
            title='Public Entry',
            content='Text',
            category=self.category,
            is_published=True
        )
        draft_entry = Entry.objects.create(
            author=self.user,
            title='Draft Entry',
            content='Text',
            category=self.category,
            is_published=False
        )

        response = self.client.get(reverse('journal:drafts'))
        drafts_list = response.context['drafts']

        self.assertIn(draft_entry, drafts_list)
        self.assertNotIn(public_entry, drafts_list)
        self.assertEqual(drafts_list.count(), 1)

    def test_draft_list_view_pagination(self):
        """Проверяем корректность paginate_by"""
        page_size = DraftListView.paginate_by

        for i in range(page_size + 1):
            Entry.objects.create(
                author=self.user,
                title=f'Draft Entry {i}',
                content='text',
                category=self.category,
                is_published=False
            )

        response = self.client.get(reverse('journal:drafts'))

        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['drafts']), page_size)

    def test_draft_list_only_users_entries(self):
        """Проверяем что черновики показывают только записи текущего пользователя"""
        user_a = User.objects.create_user('user_a', password='pass')
        user_b = User.objects.create_user('user_b', password='pass')
        
        self.client.login(username='user_a', password='pass')
        entry_a = Entry.objects.create(
                author=user_a,
                title='Draft Entry a',
                content='text',
                category=self.category,
                is_published=False
        )

        self.client.login(username='user_b', password='pass')
        entry_b = Entry.objects.create(
                author=user_b,
                title='Draft Entry b',
                content='text',
                category=self.category,
                is_published=False
        )
        
        response = self.client.get(reverse('journal:drafts'))
        self.assertNotIn(entry_a, response.context['drafts'])
        self.assertIn(entry_b, response.context['drafts'])

    def test_anonim_draft_list_view(self):
        """Проверяем что анонима перенаправляет на страницу аутентификации"""
        self.client.logout()

        response = self.client.get(reverse('journal:drafts'))
        self.assertRedirects(response, '/accounts/login/?next=/drafts/')


class EntryLogViewTest(TestCase):
    def setUp(self):        
        self.user = User.objects.create_user('test', password='pass')
        self.admin_group, _ = Group.objects.get_or_create(name='Administrator')
        self.client.login(username='test', password='pass')

    def test_entry_log_block_anonim_user(self):
        """Проверка что анонима не пустит в EntryLogView"""
        self.client.logout()

        response = self.client.get(reverse('journal:entry_logs'))
        self.assertRedirects(response, '/')

    def test_entry_log_block_not_admin_user(self):
        """Проверка что пользователя без прав не пустит в EntryLogView"""
        response = self.client.get(reverse('journal:entry_logs'))
        self.assertRedirects(response, '/')

    def test_entry_log_allowed_for_admin_user(self):
        """Проверка что администратора пустит в EntryLogView"""
        self.user.groups.add(self.admin_group)
        response = self.client.get(reverse('journal:entry_logs'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'journal/entry_log_list.html')


class StatsViewTest(TestCase):
    def setUp(self):        
        self.user = User.objects.create_user('test', password='pass')
        self.admin_group, _ = Group.objects.get_or_create(name='Administrator')
        self.client.login(username='test', password='pass')

    def test_stats_block_anonim_user(self):
        """Проверка что анонима не пустит в StatsView"""
        self.client.logout()

        response = self.client.get(reverse('journal:stats'))
        self.assertRedirects(response, '/')

    def test_stats_block_not_admin_user(self):
        """Проверка что пользователя без прав не пустит в StatsView"""
        response = self.client.get(reverse('journal:stats'))
        self.assertRedirects(response, '/')

    def test_entry_log_allowed_for_admin_user(self):
        """Проверка что администратора пустит в StatsView"""
        self.user.groups.add(self.admin_group)
        response = self.client.get(reverse('journal:stats'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'journal/stats.html')
