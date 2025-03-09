from django.urls import path# 初期設定：パスを通す
from . import views # 初期設定：パスのviewを読み込む


urlpatterns = [
    path("", views.index_view, name="index"),
    path("cosme/brand_list/",views.ListbrandView.as_view(), name="list-brand"),
    path("cosme/brand_list/<int:pk>/detail/", views.BrandCosmeView.as_view(), name="brand-detail"),
    path("cosme/search/",views.SearchView.as_view(), name="search"),   
    
    path("cosme/<int:cosme_id>/review/", views.CreateReviewView.as_view(), name="create-review"),
    path("review/<int:pk>/delete/", views.DeleteReviewView.as_view(), name="delete-review"),
    path('review/<int:pk>/update/', views.UpdateReviewView.as_view(), name='update-review'),
 
    path('test_mail/', views.TestMailView.as_view(), name='test_mail'),

    path("cosme/user/my_account/",views.MyAccountView.as_view(),  name="my-account"),
    path("cosme/user/my_account/<int:brand_id>/brand_reviews/", views.Brand_ReviewListView.as_view(), name="brand-reviews"),
    path("cosme/user/my_account/<int:tag_id>/tag_reviews/", views.Tag_ReviewListView.as_view(), name="tag-reviews"),


    path("cosme/brand/cosme/",views.ListCosmereviewView.as_view(), name="list-cosme"),
    path("cosme/brand/<int:pk>/detail/", views.DetailCosmeView.as_view(), name="detail-cosme"),
    path("cosme/brand/create/", views.CreateCosmeView.as_view(), name="create-cosme"),
    path("cosme/brand/<int:pk>/delete", views.DeleteCosmeView.as_view(), name="delete-cosme"),
    path("cosme/brand/<int:pk>/update/", views.UpdateCosmeView.as_view(), name="update-cosme"),
    
    path("cosme/cosme_category/",views.List_CosmeCategoryView.as_view(), name="cosme-category"),
    path("cosme/large_category/<str:large_category>/", views.LargeCategory_ProductListView.as_view(), name="large-category_list"),
    path("cosme/medium_categories/<str:medium_categories>/", views.MediumCategory_ProductListView.as_view(), name="medium-category_list"),
    path('cosme/category/<str:sub_category>/', views.SubCategory_ProductListView.as_view(), name='sub-category_cosme-list'),
    path("cosme/tag/",views.ListTagView .as_view(), name="list-tag"),
    path("cosme/tag/<int:pk>/", views.TagCosmeView.as_view(), name="cosme-tag"),
]