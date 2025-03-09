from django.db import models

# Create your models here.

# テーブル関連
class Cosme(models.Model):
    product_name  = models.CharField(max_length=100)
    capacity = models.CharField(max_length=30, null=True, blank=True)
    reference_price = models.IntegerField()
    product_description = models.TextField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True) 
    Ingredient_list = models.TextField()
    thumbnail = models.ImageField(upload_to='cosme/', null=True, blank=True)

    # 外部キーでBrandとCategorを紐づける
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)  # null=True→消去
    category = models.ForeignKey('Category', on_delete=models.CASCADE)# null=True→消去
    tags = models.ManyToManyField('Tag', related_name="products")
    #その他
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)  # 自分の投稿のみ編集/削除可

    def __str__(self):
        return self.product_name



class Brand(models.Model):
    brand_name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # セキュリティ対策としてハッシュ化が必要
    brand_description = models.TextField(null=True, blank=True)
    tag = models.CharField(max_length=100, null=True, blank=True)
    icon = models.ImageField(upload_to='brand/brand_icons/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='brand/brand_covers/', null=True, blank=True)
    instagram_url = models.URLField(null=True, blank=True)
    twitter_url = models.URLField(null=True, blank=True)
    facebook_url = models.URLField(null=True, blank=True)
    official_website_url = models.URLField(null=True, blank=True)
    official_website_stores_url = models.URLField(null=True, blank=True)
    brand_id = models.AutoField(primary_key=True)  # 自動採番のID

    def __str__(self):
        return self.brand_name


class Category(models.Model):
    large_categories = models.CharField(max_length=100)
    medium_categories = models.CharField(max_length=100)
    sub_categories = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.large_categories} - {self.medium_categories} - {self.sub_categories}"


class Tag(models.Model):
    tag = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.tag




RATE_CHOICES = [
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5'),
]

class Review(models.Model): #レビュー機能
    cosme = models.ForeignKey(Cosme, on_delete=models.CASCADE)
    text = models.TextField()
    rate = models.IntegerField(choices=RATE_CHOICES)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def is_high_rating(self):
        return self.rate >= 4  # 4以上で高評価と判断

    def __str__(self):
        return self.text


class Email(models.Model):
    recipient = models.EmailField("送信先メールアドレス")
    sender = models.EmailField("送信元メールアドレス")
    subject = models.CharField("メールタイトル", max_length=255)
    body = models.TextField("メール本文")
    sent_at = models.DateTimeField("送信日時", auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.recipient}"


class SearchHistory(models.Model):
    keyword = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.keyword
