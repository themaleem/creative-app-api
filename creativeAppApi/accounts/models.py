from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import date
from django.conf import settings
import enum


class UserManager(BaseUserManager):
    """
    The User Manager
    """
    def _create_user(self, email, fullname, password, is_staff, is_superuser, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        now = timezone.now()
        email = self.normalize_email(email)
        fullname = fullname
        user = self.model(
            email=email,
            fullname=fullname,
            is_staff=is_staff,
            is_active=True,
            is_superuser=is_superuser,
            last_login=now,
            date_joined=now,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, fullname, password, **extra_fields):
        return self._create_user(email, fullname, password, False, False, **extra_fields)

    def create_superuser(self, email, fullname, password, **extra_fields):
        user = self._create_user(email, fullname, password, True, True, **extra_fields)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(max_length=254, unique=True)
    fullname = models.CharField(max_length=250)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname']

    objects = UserManager()

    def __str__(self):
        return self.email

    def follow_a_user(self, user_to_follow):
        # find user by slug
        try:
            user_to_follow = User.objects.get(slug=user_to_follow)
        except:
            return False, 'User not found'

        if user_to_follow != self:
            try:
                log = FollowLog.objects.get(
                    user=user_to_follow,
                    followed_by=self,
                )
                log.set_as_followed()
                return True, 'Refollow successful'
            except:
                FollowLog.objects.create(
                    user=user_to_follow,
                    followed_by=self,
                    status=FollowStatus.following.value
                )
                return True, 'Follow Successful'
        else:
            return False, 'Cannot follow oneself'

    def unfollow_a_user(self, user_to_unfollow):
        # find user by slug
        try:
            user_to_unfollow = User.objects.get(slug=user_to_unfollow)
        except:
            return False, 'User not found'

        if user_to_unfollow != self:
            try:
                log = FollowLog.objects.get(
                    user=user_to_unfollow,
                    followed_by=self,
                )
                log.set_as_unfollowed()
                return True, 'UnFollow Successful'
            except Exception as e:
                return False, 'User doesnt follow the specified user' if 'exist' in e else e
        else:
            return False, 'Cannot unfollow oneself'

    def get_followers(self, slug):
        try:
           result = (log.followed_by.slug for log in (User.objects.get(slug=slug)).followers.all().filter(status='following'))
        except Exception:
            return '400', None
        return '200', result

    def get_followed_users(self, slug):
        try:
           result = (log.user.slug for log in (User.objects.get(slug=slug)).following.all().filter(status='following'))
        except Exception:
            return '400', None
        return '200', result
    
    def get_users_follow_count(self, slug):
        followers_count = (User.objects.get(slug=slug)).followers.all().filter(status='following').count()
        following_count = (User.objects.get(slug=slug)).following.all().filter(status='following').count()
        return '200', followers_count, following_count


class Skill(models.Model):
    name = models.CharField(max_length=300)
    created_on = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name


class Profile(models.Model):
    '''
    Note:
    profile photo is expecting photos link gotten from cloudnairy from the frontend
    - The height is calculated in feets and inches
    - Need to sort out location (lives in)
    - Need to add an age function
    - Need to add achievemnet as a foreign field 
    - Need to add education also as a foreign field
    - Add follow functionality
    '''

    SEX = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    BODYTYPE = (
        ('Slim', 'Slim'),
        ('Average', 'Average'),
        ('Athletic', 'Athletic'),
        ('Heavyset', 'Heavyset'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profiles')
    date_of_birth = models.DateField(blank=True, verbose_name="DOB", null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    profile_photo = models.CharField(blank=True, max_length=300, null=True)
    skills = models.ManyToManyField(Skill, related_name='skills')
    sex = models.CharField(max_length=1, choices=SEX, blank=True, null=True)
    type_of_body = models.CharField(max_length=8, choices=BODYTYPE, blank=True, null=True)
    feet = models.PositiveIntegerField(blank=True, null=True)
    inches = models.PositiveIntegerField(blank=True, null=True)
    lives_in = models.CharField(max_length=50, blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.fullname


class FollowStatus(enum.Enum):
    following = 'following'
    unfollowed = 'unfollowed'
    blocked = 'blocked'


FOLLOW_STATUS = (
    ('following', 'following'),
    ('unfollowed', 'unfollowed'),
    ('blocked', 'blocked'),
)


class FollowLog(models.Model):
    """
        users is intentionally using a related name of follwers sp we can query all data via the related_query_manager

        Azeem is the main guy,
        Jide is following azeem

        azeem.followers.all()

        The followed by uses a following related name

        jide.following.all()
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    followed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='following', null=True)
    followed_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=FOLLOW_STATUS, default=FollowStatus.following.value, max_length=30)
    updated_on = models.DateTimeField(auto_now=True)
    unfollowed_on = models.DateTimeField(null=True)
    blocked_on = models.DateTimeField(null=True)

    def __str__(self):
        return "{} followed by {} ".format(self.user, self.followed_by)

    def set_as_followed(self):
        self.status = FollowStatus.following.value
        self.save()

    def set_as_blocked(self):
        self.status = FollowStatus.blocked.value
        self.blocked_on = timezone.now()
        self.save()

    def set_as_unfollowed(self):
        self.status = FollowStatus.unfollowed.value
        self.unfollowed_on = timezone.now()
        self.save()
