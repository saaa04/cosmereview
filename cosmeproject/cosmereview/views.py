from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth import logout

# Create your views here.

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    DeleteView,
    UpdateView,
    TemplateView,
    FormView,
    )
from .models import Cosme, Review ,Brand, Category, Tag, Email, SearchHistory


from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin #ﾛｸﾞｲﾝ者のみ権限付与

from django.core.exceptions import PermissionDenied #自分投稿のみ編集/削除可 #PermissionDenied：ｱｸｾｽ権限

from .forms import CosmeSearchForm, TestMailForm
from django.db.models import Avg, Count, Q
from collections import Counter

from django.core.mail import send_mail
from django.conf import settings





# TOPページ
def index_view(request):
    form = CosmeSearchForm(request.GET or None)  # 検索フォームのインスタンス
    products = Cosme.objects.order_by("-id")  # 新着順に商品を取得

    # よく検索されるワードトップ5を取得
    top_5_keywords = (
        SearchHistory.objects.values('keyword')
        .annotate(count=Count('keyword'))
        .order_by('-count')[:5]
    )
 

    # 全体のレビューTOP5の商品
    top_5_products = (
        products.annotate(avg_rating=Avg('review__rate'))
        .order_by('-avg_rating')[:5]  # 平均評価の高い順
    )

    # 各 medium_category ごとのランキングTOP3を取得
    medium_categories_top3 = {}
    categories = products.values_list('category__medium_categories', flat=True).distinct()
    for category in categories:
        top3_products = (
            products.filter(category__medium_categories=category)
            .annotate(avg_rating=Avg('review__rate'))
            .order_by('-avg_rating')[:3]
        )
        medium_categories_top3[category] = top3_products

    return render(
        request,
        "cosmereview/index.html",
        {
            "form": form,
            "top_5_keywords": top_5_keywords,
            "object_list": products,
            "top_5_products": top_5_products,
            "medium_categories_top3": medium_categories_top3,
        },
    )
    

    



# 全体ページ
class SearchView(ListView):
    model = Cosme
    template_name = "cosmereview/search.html"
    context_object_name = "search_results"

    def get_queryset(self): # 検索条件でﾌｨﾙﾀﾘﾝｸﾞ
        query = self.request.GET.get("q") #ﾕｰｻﾞｰが検索したﾜｰﾄﾞを取得
        queryset = Cosme.objects.all() #全商品情報を取得

        # 検索クエリが存在する場合のフィルタリング
        if query:
            SearchHistory.objects.create(keyword=query)
            
            queryset = queryset.filter( # |（OR）いずれかの条件に該当したら
                Q(product_name__icontains=query) |
                Q(Ingredient_list__icontains=query) |
                Q(brand__brand_name__icontains=query) |
                Q(tags__tag__icontains=query)
            ).distinct()

        # 各商品にレビュー評価とレビュー件数を追加し、並び順を指定
        queryset = queryset.annotate(
            avg_rating=Avg('review__rate'),  # レビューの平均値計算
            review_count=Count('review')     # レビューの件数カウント
        ).order_by('-avg_rating', '-review_count')  # レビューレートの降順、口コミ数の降順

        return queryset







class List_CosmeCategoryView (TemplateView): #商品カテゴリ毎に表示
    template_name = "cosmereview/cosme_category.html"
    model = Category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Categoryテーブルの全データを取得
        categories = Category.objects.all()

        # カテゴリーを大・中カテゴリーでグループ化
        grouped_cosme_categories = {} #カテゴリーを「大→中→小」に分類して格納
        for category in categories:
            if category.large_categories not in grouped_cosme_categories:
                grouped_cosme_categories[category.large_categories] = {}
            if category.medium_categories not in grouped_cosme_categories[category.large_categories]:
                grouped_cosme_categories[category.large_categories][category.medium_categories] = []
            grouped_cosme_categories[category.large_categories][category.medium_categories].append(category.sub_categories)

        # コンテキストに追加
        context['grouped_cosme_categories'] = grouped_cosme_categories
        return context

#  Large/Medium/Sub ｶﾃｺﾞﾘｰ別 全商品ランキング順表示
class LargeCategory_ProductListView(ListView):
    model = Cosme
    template_name = 'cosmereview/cosme_large_category.html'
    context_object_name = 'products'

    def get_queryset(self):
        large_category = self.kwargs['large_category']
        categories = Category.objects.filter(large_categories=large_category)
        return Cosme.objects.filter(category__in=categories).annotate(
            avg_rating=Avg('review__rate'),
            review_count=Count('review')
        ).order_by('-avg_rating', '-review_count')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['large_category'] = self.kwargs['large_category']
        return context


class MediumCategory_ProductListView(ListView):
    model = Cosme
    template_name = 'cosmereview/cosme_medium_categories.html'
    context_object_name = 'products'

    def get_queryset(self):
        medium_categories = self.kwargs['medium_categories']
        categories = Category.objects.filter(medium_categories=medium_categories)
        return Cosme.objects.filter(category__in=categories).annotate(
            avg_rating=Avg('review__rate'),
            review_count=Count('review')
        ).order_by('-avg_rating', '-review_count')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medium_categories'] = self.kwargs['medium_categories']
        return context


class SubCategory_ProductListView(ListView):
    model = Cosme
    template_name = 'cosmereview/cosme_sub_category.html'
    context_object_name = 'products' #HTMLがｵﾌﾞｼﾞｪｸﾄを取得する際の名前
    
    def get_queryset(self):
        # URLの sub_category パラメータを取得し、該当するカテゴリを取得
        sub_category = self.kwargs['sub_category'] # sub_categoryｷｰでURLから取得したｶﾃｺﾞﾘ名を取得 #URL例：/category/化粧水/
        category = get_object_or_404(Category, sub_categories=sub_category) # ↑ﾓﾃﾞﾙが無い→404エラー表示

        # 該当カテゴリの商品をレビュー平均とレビュー数でソートして取得
        queryset = Cosme.objects.filter(category=category).annotate( # 該当categoryﾃﾞｰﾀ取得
            avg_rating=Avg('review__rate'), #ﾚﾋﾞｭｰレート計算
            review_count=Count('review') # ﾚﾋﾞｭｰ数カウント
        ).order_by('-avg_rating', '-review_count') #ﾚﾋﾞｭｰレート,数が大きい順に

        return queryset

    def get_context_data(self, **kwargs): # ↑ get_context_dataで定義→コンテキスト化
        context = super().get_context_data(**kwargs)
        # カテゴリ名をコンテキストに追加
        context['category'] = get_object_or_404(Category, sub_categories=self.kwargs['sub_category'])
        return context


class BrandCosmeView(DetailView):
    model = Brand
    template_name = "cosmereview/brand_detail.html"
    context_object_name = "brand"
   
    def get_object(self):
        return get_object_or_404(Brand, pk=self.kwargs['pk']) # pkを元にbrand情報を取得。無いver.404エラー表示

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.get_object() # ブランド情報を取得
        
        # デバッグ用にブランドの全商品を取得し、ログを出力
        cosme_queryset = Cosme.objects.filter(brand=brand)
        print(f"ブランドの商品数: {cosme_queryset.count()}")  # デバッグで商品数を確認

        # medium_categories名を重複なく取得
        categories = (
            cosme_queryset
            .values_list('category__medium_categories', flat=True) #重複を除外
            .distinct()
        )
        print(f"取得したカテゴリ一覧: {list(categories)}")  # デバッグでカテゴリlistを確認

        # 各mediumカテゴリごとのレビューTOP3商品
        medium_categories_top3 = {} # ｶﾃｺﾞﾘｰ/数字変更可
        for category in categories:
            top3_products = (
                cosme_queryset.filter(category__medium_categories=category) # ｶﾃｺﾞﾘｰ変更可
                .annotate(avg_rate=Avg('review__rate')) #各商品の平均レビュレート計算
                .order_by('-avg_rate')[:3] #レビューレートTOP３取得 # 数字変更可
            )
            medium_categories_top3[category] = top3_products 


        # ブランド全体のレビューTOP5の商品
        top_5_products = ( # 数字変更可
            Cosme.objects.filter(brand=brand)
            .annotate(avg_rate=Avg('review__rate'))
            .order_by('-avg_rate')[:5] # 数字変更可 (表示される個数)
        )


        context["top_5_products"] = top_5_products
        context["medium_categories_top3"] = medium_categories_top3
        return context


class TagCosmeView(DetailView):
    model = Tag
    template_name = "cosmereview/cosme_tag.html"
    context_object_name = "tag"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 関連する商品をレビューの平均評価と総数で取得
        products = (
            Cosme.objects.filter(tags=self.object)
            .annotate(
                avg_rating=Avg('review__rate'),  # レビューの平均評価
                review_count=Count('review')     # レビューの総数
            )
            .order_by('-avg_rating')  # 平均評価の高い順に並べる
        )

        context['products'] = products
        return context



# userページ
class MyAccountView(TemplateView):
    template_name = 'accounts/user_my_account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ブランドランキング（レビューレート順、次にレビュー数の多い順）
        brand_rankings = (
            Brand.objects
            .filter(cosme__review__user=self.request.user)
            .annotate(
                avg_rating=Avg('cosme__review__rate'),
                review_count=Count('cosme__review')
            )
            .order_by('-avg_rating', '-review_count')[:3]
        )
        
        # ユーザーがレビューした商品についているタグの集計
        top_tags = (
            Tag.objects
            .filter(products__review__user=self.request.user)  # ユーザーがレビューした商品に関連するタグ
            .annotate(tag_count=Count('products__review'))      # タグの出現回数をカウント
            .order_by('-tag_count')[:15]                        # 出現回数が多い順でTOP15を取得
        )


        # ユーザーがレビューで3.5以上をつけた商品の成分リストを集計
        ingredients_counter = Counter()
        high_rated_products = (
            Cosme.objects
            .filter(review__user=self.request.user, review__rate__gte=3.5)
        )

        for product in high_rated_products:
            ingredients = product.Ingredient_list.split(',')  # カンマ区切りで成分を分割
            ingredients = [ingredient.strip() for ingredient in ingredients]  # 空白を除去
            ingredients_counter.update(ingredients)

        # 上位30の成分とそのカウントを取得
        top_ingredients = ingredients_counter.most_common(30)


        context['brand_rankings'] = brand_rankings
        context['top_tags'] = top_tags
        context['top_ingredients'] = top_ingredients
        return context


class Brand_ReviewListView(LoginRequiredMixin, ListView):
    template_name = "accounts/brand_review_list.html"
    context_object_name = "reviews"

    def get_queryset(self): #ログインﾕｰｻﾞｰとbrand_idから該当レビューを取得
        # brand_id を主キーとして使用
        brand_id = self.kwargs['brand_id'] #URLから取得したbrand_idから識別する
        user = self.request.user #ログインﾕｰｻﾞｰを識別
        return Review.objects.filter(cosme__brand__brand_id=brand_id, user=user).select_related('cosme')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # brand_id を使用して Brand オブジェクトを取得 → 「brand」がHTMLで使用できる
        context['brand'] = Brand.objects.get(brand_id=self.kwargs['brand_id'])
        return context


class Tag_ReviewListView(LoginRequiredMixin, ListView):
    template_name = "accounts/tag_review_list.html"
    context_object_name = "reviews"

    def get_queryset(self): #ログインﾕｰｻﾞｰとtag_idから該当レビューを取得
        tag_id = self.kwargs['tag_id'] #URLから取得したtag_idから識別する
        user = self.request.user #ログインﾕｰｻﾞｰを識別
        return Review.objects.filter(cosme__tags__id=tag_id, user=user).select_related('cosme')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # tag_id を使用して Tag オブジェクトを取得 → 「tag」がHTMLで使用できる
        context['tag'] = Tag.objects.get(id=self.kwargs['tag_id'])
        return context



# brandページ
class ListCosmereviewView(ListView):
    template_name = "cosmereview/cosme_list.html"
    model = Cosme

    def get_queryset(self):
        # 各商品に関連付けられているレビュー数と平均評価を注釈
        queryset = (
            super().get_queryset()
            .annotate(
                review_count=Count('review'),  # レビュー数
                avg_rating=Avg('review__rate')  # 平均評価
            )
        )
        return queryset 
    
    def get(self, request, *args, **kwargs):
        # `cosme_id`がURLパラメータに含まれている場合はリダイレクト処理
        cosme_id = request.GET.get('cosme_id')
        if cosme_id:
            cosme = get_object_or_404(Cosme, pk=cosme_id)
            try:
                review = Review.objects.get(cosme=cosme, user=request.user) # ユーザーが該当商品にレビューを作成していたか確認
                return redirect('update-review', pk=review.pk)  # 既存レビューがあるver.編集ページにリダイレクト
            except Review.DoesNotExist:
                return redirect('create-review', cosme_id=cosme.id)  # 既存レビューがないver.作成ページにリダイレクト
        # 通常のリスト表示を実行
        return super().get(request, *args, **kwargs) #エラー時：cosme_idがないver.標準のリストビュー処理（cosme_list.htmlへ）

 
 
    

class DetailCosmeView(DetailView):
    template_name = "cosmereview/cosme_detail.html"
    model = Cosme
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 商品に関連するレビュー件数を計算
        context['reviews'] = self.object.review_set.select_related('user').all()
        context['review_count'] = self.object.review_set.count()
        return context
    

class CreateCosmeView(LoginRequiredMixin,CreateView):
    template_name = "cosmereview/cosme_create.html"
    model = Cosme
    fields = (
                "product_name", 
                "capacity",
                "reference_price",
                "product_description",
                "release_date",
                "Ingredient_list",
                'thumbnail',
                "brand",
                "category",
                "tags",
            )
    success_url = reverse_lazy("list-cosme")
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form) # form_valid(form):ﾕｰｻﾞｰ情報追記


class DeleteCosmeView(LoginRequiredMixin,DeleteView):
    template_name = "cosmereview/cosme_confirm_delete.html"
    model = Cosme
    success_url = reverse_lazy("list-cosme")

    def get_object(self, queryset=None): # ｵｰﾅｰ以外が削除を試みると遷移する
        obj = super().get_object(queryset)

        if obj.user != self.request.user:
            raise PermissionDenied

        return obj


    
class UpdateCosmeView(LoginRequiredMixin,UpdateView):
    model = Cosme
    fields = (
                "product_name", 
                "capacity",
                "reference_price",
                "product_description",
                "release_date",
                "Ingredient_list",
                'thumbnail',
                "brand",
                "category",
                "tags",
            )
    
    template_name = "cosmereview/cosme_update.html"
    success_url = reverse_lazy("list-cosme")
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if obj.user != self.request.user: # 商品ｵｰﾅｰと不一致 => error
            raise PermissionDenied

        return obj
    
    def get_success_url(self): # ｵｰﾅｰ以外が編集を試みると遷移する
        return reverse('detail-cosme', kwargs={'pk': self.object.id})




class CreateReviewView(LoginRequiredMixin, CreateView):
    model = Review
    fields = ('cosme', 'text', 'rate')
    template_name = 'cosmereview/review_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cosme'] = Cosme.objects.get(pk=self.kwargs['cosme_id']) #cosme_idから商品にｱｸｾｽ
        return context

    def form_valid(self, form): 
        form.instance.user = self.request.user #レビュー投稿者を記録
        response = super().form_valid(form) #レビュー内容をDBに保存
        self.send_review_mail(form.instance) # 高評価者にメール送信
        return response

    def get_success_url(self): #レビュー後のﾘﾀﾞｲﾚｸﾄ先指定
        return reverse('detail-cosme', kwargs={'pk': self.object.cosme.id})

    def send_review_mail(self, review): #メール内容を定義
        if review.is_high_rating():
            # メールの基本設定
            product_name = review.cosme.product_name
            subject = f"{product_name}にレビューありがとうございます。"
            
            # 好きなブランドの商品を取得
            favorite_brands = (
                Brand.objects
                .filter(cosme__review__user=review.user)
                .annotate(
                    avg_rating=Avg('cosme__review__rate'),
                    review_count=Count('cosme__review')
                )
                .order_by('-avg_rating', '-review_count')[:3] #平均評価が高く、ﾚﾋﾞｭｰ回数多いTOP３
            )
            
            # 好きなブランドで人気の商品リスト
            brand_recommendations = []
            for brand in favorite_brands:
                popular_products = (
                    Cosme.objects
                    .filter(brand=brand)
                    .annotate(avg_rating=Avg('review__rate'))
                    .order_by('-avg_rating')[:1]
                )
                for product in popular_products:
                    brand_recommendations.append(f"- {product.product_name}（{brand.brand_name}）") #商品名、ブランド名

            # 興味のあるタグの商品を取得
            top_tags = (
                Tag.objects
                .filter(products__review__user=review.user)
                .annotate(tag_count=Count('products__review'))
                .order_by('-tag_count')[:5] #タグ頻出回数TOP５
            )
            
            # 興味のあるタグで人気の商品リスト
            tag_recommendations = []
            for tag in top_tags:
                popular_products = (
                    Cosme.objects
                    .filter(tags=tag)
                    .annotate(avg_rating=Avg('review__rate'))
                    .order_by('-avg_rating')[:1]
                )
                for product in popular_products:
                    tag_recommendations.append(f"- {product.product_name}（タグ: {tag.tag}）") #商品名、選んだタグ

            # メール本文の生成内容
            message = f"""
            {product_name}にレビューありがとうございます。

            私らしいスキをあなたに。
            特別クーポンだよ！
            ┌────────────────┐
                1000円OFF
                & 送料無料
                クーポンコード: review1000
            └────────────────┘
            ※8,000円以上で適用
            ログインして使ってね♡
            http://

            あなたへのオススメ
            好きなブランドで人気の商品
            {''.join(brand_recommendations)}

            興味のあるタグで人気の商品
            {''.join(tag_recommendations)}
            """

            # メール送信
            sender = settings.DEFAULT_FROM_EMAIL
            recipient = review.user.email
            send_mail(subject, message, sender, [recipient])
            
            # 送信履歴を保存
            Email.objects.create(
                recipient=recipient,
                sender=sender,
                subject=subject,
                body=message
            )


class DeleteReviewView(LoginRequiredMixin,DeleteView):
    template_name = "cosmereview/review_delete.html"
    model = Review
    success_url = reverse_lazy("my-account")

    def get_object(self, queryset=None): # ｵｰﾅｰ以外が削除を試みると遷移する
        obj = super().get_object(queryset)

        if obj.user != self.request.user:
            raise PermissionDenied

        return obj
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cosme_name'] = self.object.cosme.product_name  # 商品名
        context['review_text'] = self.object.text  # レビュー文
        return context


    
class UpdateReviewView(LoginRequiredMixin, UpdateView):
    model = Review
    fields = ('text', 'rate') #cosmeは編集できない
    template_name = "cosmereview/review_update.html"
    success_url = reverse_lazy("my-account")

    def get_object(self, queryset=None): # 対象ﾚﾋﾞｭｰ情報の取得
        obj = super().get_object(queryset) #親クラス(UpdateView) の get_object を呼び、ﾚﾋﾞｭｰのｲﾝｽﾀﾝｽ化
        if obj.user != self.request.user: # ﾚﾋﾞｭｰ投稿者 (obj.user) が現ﾕｰｻﾞｰ (self.request.user) と一致しているか確認
            raise PermissionDenied # ﾕｰｻﾞｰが操作権限がない時のエラー
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cosme'] = self.object.cosme # 固定表示するCosme情報をﾃﾝﾌﾟﾚｰﾄに渡す
        return context



class TestMailView(FormView):
    form_class = TestMailForm
    template_name = 'email/test_mail.html'
    success_url = '/success/'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        subject = "テストメール"
        message = "このメールはテスト送信です。"
        sender = settings.DEFAULT_FROM_EMAIL

        # メールを送信
        send_mail(subject, message, sender, [email])

        # 送信履歴を保存
        Email.objects.create(
            recipient=email,
            sender=sender,
            subject=subject,
            body=message
        )

        return super().form_valid(form)

        
  

class ListbrandView (ListView):
    template_name = "cosmereview/brand_list.html"
    model = Brand
    context_object_name = "brands"
    
class ListTagView (ListView):
    template_name = "cosmereview/tag_list.html"
    model = Tag
    context_object_name = "tags"


    

