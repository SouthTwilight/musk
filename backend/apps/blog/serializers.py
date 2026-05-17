from rest_framework import serializers
from apps.blog.models import (
    Category, RSSSource, Article, FailedURL, BlogConfig, ScoreDimension,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "icon", "score_thresholds", "article_count")
        read_only_fields = ("id", "article_count")

    def create(self, validated_data):
        using = validated_data.pop("using", "default")
        return Category.objects.using(using).create(**validated_data)

    def update(self, instance, validated_data):
        using = validated_data.pop("using", "default")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        return instance


class RSSSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSSSource
        fields = (
            "id", "name", "url", "category", "fetch_interval",
            "last_fetched", "is_active", "created_at",
        )
        read_only_fields = ("id", "last_fetched", "created_at")

    def create(self, validated_data):
        using = validated_data.pop("using", "default")
        return RSSSource.objects.using(using).create(**validated_data)

    def update(self, instance, validated_data):
        using = validated_data.pop("using", "default")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        return instance


class ArticleListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", default="")
    category_icon = serializers.CharField(source="category.icon", default="")

    class Meta:
        model = Article
        fields = (
            "id", "title", "url", "category", "category_name", "category_icon",
            "status", "score", "source_name", "summary",
            "published_at", "created_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ArticleDetailSerializer(ArticleListSerializer):
    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + (
            "key_points", "deep_analysis", "raw_text",
        )

    def update(self, instance, validated_data):
        validated_data.pop("category_name", None)
        validated_data.pop("category_icon", None)
        using = validated_data.pop("using", "default")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        return instance


class FailedURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = FailedURL
        fields = ("id", "url", "reason", "attempted_at")
        read_only_fields = ("id", "attempted_at")

    def create(self, validated_data):
        using = validated_data.pop("using", "default")
        return FailedURL.objects.using(using).create(**validated_data)


class BlogConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogConfig
        fields = ("id", "key", "value")
        read_only_fields = ("id",)

    def create(self, validated_data):
        using = validated_data.pop("using", "default")
        return BlogConfig.objects.using(using).create(**validated_data)

    def update(self, instance, validated_data):
        using = validated_data.pop("using", "default")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        return instance


class ScoreDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreDimension
        fields = ("id", "name", "description", "weight")
        read_only_fields = ("id",)

    def create(self, validated_data):
        using = validated_data.pop("using", "default")
        return ScoreDimension.objects.using(using).create(**validated_data)

    def update(self, instance, validated_data):
        using = validated_data.pop("using", "default")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using=using)
        return instance


class FetchURLSerializer(serializers.Serializer):
    url = serializers.URLField()
    category_id = serializers.IntegerField(required=False, allow_null=True)
