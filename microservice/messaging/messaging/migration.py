# Generated manually for messaging service

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_type', models.CharField(choices=[('administrator', 'Administrator'), ('teacher', 'Teacher'), ('student', 'Student'), ('parent', 'Parent')], max_length=15)),
                ('sender_id', models.IntegerField()),
                ('recipient_type', models.CharField(choices=[('administrator', 'Administrator'), ('teacher', 'Teacher'), ('student', 'Student'), ('parent', 'Parent')], max_length=15)),
                ('recipient_id', models.IntegerField()),
                ('content', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('participant1_type', models.CharField(choices=[('administrator', 'Administrator'), ('teacher', 'Teacher'), ('student', 'Student'), ('parent', 'Parent')], max_length=15)),
                ('participant1_id', models.IntegerField()),
                ('participant2_type', models.CharField(choices=[('administrator', 'Administrator'), ('teacher', 'Teacher'), ('student', 'Student'), ('parent', 'Parent')], max_length=15)),
                ('participant2_id', models.IntegerField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conversation_last_message', to='messaging.message')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['sender_type', 'sender_id'], name='messaging_me_sender__f4d8a8_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['recipient_type', 'recipient_id'], name='messaging_me_recipie_9b1a85_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['created_at'], name='messaging_me_created_1c4e8f_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['is_read'], name='messaging_me_is_read_a8b7c6_idx'),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['participant1_type', 'participant1_id'], name='messaging_co_partici_7b6f91_idx'),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['participant2_type', 'participant2_id'], name='messaging_co_partici_a2c5e9_idx'),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['updated_at'], name='messaging_co_updated_d4e8b7_idx'),
        ),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.UniqueConstraint(fields=('participant1_type', 'participant1_id', 'participant2_type', 'participant2_id'), name='unique_conversation'),
        ),
    ]