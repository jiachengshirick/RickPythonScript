#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能新闻评论生成器
功能：分析新闻内容，生成有趣的评论，并配套相关图片
"""

import requests
import json
import re
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import openai
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from typing import Dict, List, Optional, Tuple
import praw
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsAnalysis:
    """新闻分析结果数据类"""
    humor_points: List[str]  # 笑点
    criticism_points: List[str]  # 槽点
    core_viewpoints: List[str]  # 核心观点
    controversial_points: List[str]  # 争议点
    key_images: List[str]  # 关键图片URL
    summary: str  # 文章摘要


@dataclass
class RedditReference:
    """Reddit参考评论数据类"""
    comment: str
    score: int
    awards: int
    subreddit: str
    style: str  # 评论风格标签


@dataclass
class GeneratedComment:
    """生成的评论数据类"""
    content: str
    style: str  # 风格：provocative, witty, insightful, question
    image_prompt: str  # 配套图片描述
    confidence: float  # 质量评分


class NewsContentExtractor:
    """新闻内容提取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def extract_content(self, url: str) -> Dict:
        """提取新闻内容和图片"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # 提取标题
            title = self._extract_title(soup)

            # 提取正文
            content = self._extract_article_text(soup)

            # 提取图片
            images = self._extract_images(soup, url)

            return {
                'title': title,
                'content': content,
                'images': images,
                'url': url
            }

        except Exception as e:
            raise Exception(f"内容提取失败: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        selectors = ['h1', '.title', '#title', '[class*="title"]', 'title']
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        return "未找到标题"

    def _extract_article_text(self, soup: BeautifulSoup) -> str:
        """提取文章正文"""
        # 移除不需要的标签
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()

        # 尝试多种正文选择器
        content_selectors = [
            '[class*="content"]', '[class*="article"]', '[class*="story"]',
            '[id*="content"]', '[id*="article"]', 'main', '.post-content'
        ]

        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                text = ' '.join([elem.get_text() for elem in elements])
                if len(text) > 200:  # 确保内容足够长
                    return self._clean_text(text)

        # 备用方案：提取所有p标签
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = ' '.join([p.get_text() for p in paragraphs])
            return self._clean_text(text)

        return soup.get_text()[:2000]  # 限制长度

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取图片URL"""
        images = []
        img_tags = soup.find_all('img')

        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src:
                full_url = urljoin(base_url, src)
                if self._is_valid_image(full_url):
                    images.append(full_url)

        return images[:5]  # 限制图片数量

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        text = re.sub(r'\s+', ' ', text)  # 合并空白字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()"""''—-]', '', text)  # 保留中英文和常用标点
        return text.strip()

    def _is_valid_image(self, url: str) -> bool:
        """检查是否为有效图片URL"""
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        return any(url.lower().endswith(ext) for ext in valid_extensions)


class NewsAnalyzer:
    """新闻内容分析器"""

    def __init__(self, api_key: str):
        openai.api_key = api_key

    def analyze_news(self, title: str, content: str) -> NewsAnalysis:
        """分析新闻内容，识别各种要点"""

        prompt = f"""
        请用中文分析以下新闻内容，识别出：
        1. 笑点（有趣、搞笑的部分）
        2. 槽点（值得吐槽、批评的地方）
        3. 核心观点（文章的主要论点）
        4. 潜在争议点（可能引起争议的内容）

        标题：{title}
        内容：{content[:2000]}

        请以JSON格式返回，包含以下字段：
        - humor_points: 笑点列表
        - criticism_points: 槽点列表
        - core_viewpoints: 核心观点列表
        - controversial_points: 争议点列表
        - summary: 文章摘要（50字以内）
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻分析师，善于识别新闻中的各种要点。请用中文分析，并请始终返回标准JSON格式内容，不要添加任何注释或markdown格式，不加解释和任何说明。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            raw_content = response.choices[0].message.content.strip()

            # 如果以```开头，去除Markdown代码块
            if raw_content.startswith("```"):
                raw_content = re.sub(r"^```(?:json)?\s*", "", raw_content)  # 移除起始 ```
                raw_content = re.sub(r"\s*```$", "", raw_content)  # 移除结束 ```

            result = json.loads(raw_content)

            return NewsAnalysis(
                humor_points=result.get('humor_points', []),
                criticism_points=result.get('criticism_points', []),
                core_viewpoints=result.get('core_viewpoints', []),
                controversial_points=result.get('controversial_points', []),
                key_images=[],  # 将在后续填充
                summary=result.get('summary', '')
            )

        except Exception as e:
            print(f"新闻分析失败: {e}")
            return NewsAnalysis([], [], [], [], [], "分析失败")


class RedditMiner:
    """Reddit评论挖掘器"""

    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    def find_related_discussions(self, keywords: List[str], limit: int = 10) -> List[RedditReference]:
        """根据关键词搜索相关Reddit讨论"""
        references = []

        # 组合关键词进行搜索
        query = ' OR '.join(keywords[:3])  # 限制关键词数量

        try:
            # 搜索热门帖子
            for submission in self.reddit.subreddit('all').search(query, limit=limit, sort='hot'):
                # 获取高质量评论
                submission.comments.replace_more(limit=0)  # 展开评论

                for comment in submission.comments[:5]:  # 取前5个评论
                    if len(comment.body) > 50 and comment.score > 10:
                        style = self._classify_comment_style(comment.body)

                        references.append(RedditReference(
                            comment=comment.body[:300],  # 限制长度
                            score=comment.score,
                            awards=len(comment.all_awardings) if hasattr(comment, 'all_awardings') else 0,
                            subreddit=submission.subreddit.display_name,
                            style=style
                        ))

            # 按热度排序
            references.sort(key=lambda x: x.score + x.awards * 10, reverse=True)
            return references[:5]  # 返回最热门的5个

        except Exception as e:
            print(f"Reddit搜索失败: {e}")
            return []

    def _classify_comment_style(self, comment: str) -> str:
        """分类评论风格"""
        comment_lower = comment.lower()

        # 引战型
        if any(word in comment_lower for word in ['stupid', 'wrong', 'disagree', 'ridiculous']):
            return 'provocative'

        # 幽默型
        elif any(word in comment_lower for word in ['lol', 'funny', 'joke', 'haha', '😂']):
            return 'witty'

        # 提问型
        elif comment.count('?') >= 2:
            return 'question'

        # 深刻型
        elif len(comment) > 200:
            return 'insightful'

        return 'neutral'


class CommentGenerator:
    """评论生成器"""

    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.styles = ['provocative', 'witty', 'insightful', 'question']

    def generate_comments(self, analysis: NewsAnalysis, reddit_refs: List[RedditReference]) -> List[GeneratedComment]:
        """生成多种风格的评论"""
        comments = []

        # 为每种风格生成一个评论
        for style in self.styles:
            comment = self._generate_single_comment(analysis, reddit_refs, style)
            if comment:
                comments.append(comment)

        return sorted(comments, key=lambda x: x.confidence, reverse=True)

    def _generate_single_comment(self, analysis: NewsAnalysis, reddit_refs: List[RedditReference], style: str) -> \
    Optional[GeneratedComment]:
        """生成特定风格的评论"""

        # 获取相同风格的Reddit参考
        style_refs = [ref for ref in reddit_refs if ref.style == style]
        ref_text = '\n'.join([ref.comment for ref in style_refs[:2]])

        # 构建提示
        style_prompts = {
            'provocative': '生成一个有争议性、能够引起讨论的评论，要犀利但不过分',
            'witty': '生成一个机智幽默的评论，可以是双关语、讽刺或巧妙的观察',
            'insightful': '生成一个深刻有见地的评论，提供新的视角或深度分析',
            'question': '生成一个发人深省的问题，能够引发读者思考'
        }

        prompt = f"""
        # 角色
        你是一名洞察力敏锐、语言风趣的社交媒体评论员。你的任务是基于一份新闻的核心分析，创作出一条简短、犀利、易于传播的原创评论，并为之构思一个富有创意的图片描述。

        # 新闻分析材料
        - **核心观点**: {'; '.join(analysis.core_viewpoints)}
        - **争议与槽点**: {'; '.join(analysis.controversial_points + analysis.criticism_points)}
        - **幽默与笑点**: {'; '.join(analysis.humor_points)}

        # 创作指令
        1.  **评论内容**:
            - **风格**: 整体基调为 **{style_prompts[style]}**。
            - **参考**: 模仿以下例子的语气和态度，但**不要照抄**内容或句式: "{ref_text}"
            - **整合**: 巧妙地融合`新闻分析材料`中的至少一到两个关键点，形成连贯、有见地的观点。避免生硬罗列。
            - **约束**: 长度严格控制在100字以内，语言自然口语化，符合网络讨论习惯。

        2.  **图片描述 (Image Prompt)**:
            - **要求**: 构思一个具有象征性、讽刺性或戏剧性张力的画面，能够将你的评论核心思想视觉化。描述需要生动、富有想象力，便于AI绘画模型理解。

        # 输出格式
        请严格按照以下JSON格式返回，不要包含任何JSON格式之外的额外解释。
        {{
            "comment": "在这里填写你创作的评论内容",
            "image_prompt": "在这里填写你构思的图片描述",
            "confidence": 0.8
        }}
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": f"你是一个{style}风格的网络评论高手。请始终返回标准JSON格式内容，不要添加任何注释或markdown格式，不加解释和任何说明。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )

            raw_content = response.choices[0].message.content.strip()

            # 如果以```开头，去除Markdown代码块
            if raw_content.startswith("```"):
                raw_content = re.sub(r"^```(?:json)?\s*", "", raw_content)  # 移除起始 ```
                raw_content = re.sub(r"\s*```$", "", raw_content)  # 移除结束 ```

            result = json.loads(raw_content)

            return GeneratedComment(
                content=result.get('comment', ''),
                style=style,
                image_prompt=result.get('image_prompt', ''),
                confidence=result.get('confidence', 0.5)
            )

        except Exception as e:
            print(f"评论生成失败 ({style}): {e}")
            return None


class ImageGenerator:
    """图片生成器"""

    def __init__(self, config: Dict):
        self.config = config
        self.provider = config.get('image_provider', 'gpt5')  # 默认使用GPT-5

        if self.provider in ['gpt5', 'dalle']:
            openai.api_key = config['openai_api_key']
        elif self.provider == 'flux':
            # Flux API配置
            self.flux_api_key = config.get('flux_api_key')
        elif self.provider == 'firefly':
            # Adobe Firefly API配置
            self.firefly_api_key = config.get('firefly_api_key')

    def generate_comment_image(self, comment: GeneratedComment, news_title: str) -> Optional[str]:
        """为评论生成配套图片"""

        # 构建图片生成提示
        image_prompt = f"""
        请根据以下评论生成一张具有梗图风格的图片：

        评论内容：「{comment.content}」
        评论风格：{comment.style}
        新闻背景：「{news_title}」
        画面构思：{comment.image_prompt}
        如果需要生成名人肖像，请生成卡通画风的名人肖像，准确指出名人的姓名。
        请确保图片具有视觉冲击力，适合在社交媒体上传播，兼具趣味性与话题性。避免使用太多的文字，简单明了即可。
        """

        try:
            if self.provider == 'gpt5':
                return self._generate_with_gpt5(image_prompt)
            elif self.provider == 'dalle':
                return self._generate_with_dalle(image_prompt)
            elif self.provider == 'flux':
                return self._generate_with_flux(image_prompt)
            elif self.provider == 'firefly':
                return self._generate_with_firefly(image_prompt)
            else:
                raise ValueError(f"不支持的图片生成器: {self.provider}")

        except Exception as e:
            print(f"图片生成失败: {e}")
            return self._generate_text_image(comment)