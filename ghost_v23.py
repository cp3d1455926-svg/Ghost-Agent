# -*- coding: utf-8 -*-
"""
Ghost Agent v2.3 - WeChat Official Account Assistant
Author: Ghost & Jake
"""
import json, re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent
CONTENT_DIR = WORKSPACE / "content"
CONTENT_DIR.mkdir(exist_ok=True)


class ArticleWriter:
    """Write WeChat articles"""
    
    def __init__(self, account_name="Ghost", style="casual"):
        self.account_name = account_name
        self.style = style
    
    def write(self, topic, article_type="list"):
        print("[ArticleWriter] " + topic + " (" + article_type + ")")
        
        article = {
            "title": self._gen_title(topic),
            "cover_desc": topic + " - one article is enough",
            "author": self.account_name,
            "created": datetime.now().isoformat(),
            "type": article_type,
            "tags": self._gen_tags(topic),
            "sections": self._gen_sections(topic, article_type),
            "cta": self._gen_cta(),
        }
        
        # Save
        safe_name = re.sub(r'[^\w\u4e00-\u9fff]+', '_', topic)[:30]
        filename = datetime.now().strftime("%Y%m%d") + "_" + safe_name + ".json"
        filepath = CONTENT_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        
        print("  Saved: " + str(filepath.name))
        return article
    
    def _gen_title(self, topic):
        templates = [
            topic + " - One Article Guide",
            "Complete Guide to " + topic,
            "5 Things You Didn't Know About " + topic,
            topic + " Tips and Tricks",
            "Let's Talk About " + topic,
        ]
        return templates[0]
    
    def _gen_tags(self, topic):
        tags = [topic]
        if "AI" in topic or "ai" in topic:
            tags.extend(["AI", "Tech"])
        if "tool" in topic or "Tool" in topic:
            tags.extend(["Tools", "Productivity"])
        return tags[:5]
    
    def _gen_sections(self, topic, article_type):
        if article_type == "tutorial":
            return [
                {"type": "intro", "text": "Why learn " + topic + "?"},
                {"type": "prereq", "text": "What you need to get started"},
                {"type": "steps", "text": "Step-by-step guide"},
                {"type": "summary", "text": "Key takeaways"},
            ]
        elif article_type == "story":
            return [
                {"type": "hook", "text": "A story about " + topic},
                {"type": "story", "text": "The full story..."},
                {"type": "lesson", "text": "What we learned"},
            ]
        else:  # list
            return [
                {"type": "intro", "text": "Introduction to " + topic},
                {"type": "list", "items": [
                    {"title": "Point 1", "content": "Details about point 1"},
                    {"title": "Point 2", "content": "Details about point 2"},
                    {"title": "Point 3", "content": "Details about point 3"},
                ]},
                {"type": "conclusion", "text": "Summary of " + topic},
            ]
    
    def _gen_cta(self):
        return "If you found this helpful, follow us for more!"


class ContentPlanner:
    """Plan weekly content"""
    
    def plan_week(self, themes):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        plan = []
        for i, day in enumerate(days):
            theme = themes[i % len(themes)]
            plan.append({
                "day": day,
                "theme": theme,
                "type": self._suggest_type(theme),
                "status": "planned",
            })
        return plan
    
    def _suggest_type(self, theme):
        theme_l = theme.lower()
        if any(k in theme_l for k in ["tool", "app", "software", "recommend"]):
            return "list"
        elif any(k in theme_l for k in ["tutorial", "guide", "how", "tips"]):
            return "tutorial"
        elif any(k in theme_l for k in ["story", "experience", "thoughts"]):
            return "story"
        return "list"
    
    def show_calendar(self, plan):
        print("=" * 50)
        print("Content Calendar")
        print("=" * 50)
        for item in plan:
            print("  " + item["day"] + " | " + item["theme"] + " (" + item["type"] + ")")
        print()


class StyleAnalyzer:
    """Analyze article style"""
    
    def analyze(self, text):
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s for s in sentences if s.strip()]
        return {
            "char_count": len(text),
            "paragraphs": len(text.split("\n\n")),
            "sentences": len(sentences),
            "avg_sentence_len": sum(len(s) for s in sentences) / max(len(sentences), 1),
            "questions": text.count("?") + text.count("\uff1f"),
            "exclamations": text.count("!") + text.count("\uff01"),
        }


class AccountAssistant:
    """WeChat Official Account Assistant"""
    
    def __init__(self, account_name="Ghost"):
        self.account_name = account_name
        self.writer = ArticleWriter(account_name)
        self.planner = ContentPlanner()
        self.analyzer = StyleAnalyzer()
        self.articles = []
    
    def write_article(self, topic, article_type="list"):
        article = self.writer.write(topic, article_type)
        self.articles.append(article)
        return article
    
    def plan_week(self, themes):
        plan = self.planner.plan_week(themes)
        self.planner.show_calendar(plan)
        return plan
    
    def batch_write(self, topics):
        results = []
        for topic in topics:
            article = self.write_article(topic)
            results.append(article)
        print("\nBatch complete: " + str(len(results)) + " articles")
        return results
    
    def analyze_style(self, text):
        return self.analyzer.analyze(text)
    
    def dashboard(self):
        print("=" * 50)
        print("Account: " + self.account_name)
        print("Articles: " + str(len(self.articles)))
        if self.articles:
            print("Latest: " + self.articles[-1].get("title", "N/A"))
        print("=" * 50)


if __name__ == "__main__":
    import sys
    
    assistant = AccountAssistant("Ghost")
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "write" and len(sys.argv) > 2:
            article = assistant.write_article(" ".join(sys.argv[2:]))
            print("Title: " + article["title"])
        elif cmd == "plan":
            themes = ["AI Tools", "Coding Tips", "Productivity", "Tech News", "Book Review"]
            assistant.plan_week(themes)
        elif cmd == "batch":
            topics = ["10 Must-Have AI Tools", "Python Beginner Guide", "Productivity Tips"]
            assistant.batch_write(topics)
        elif cmd == "dashboard":
            assistant.dashboard()
        else:
            print("Usage: python ghost_v23.py <write|plan|batch|dashboard>")
    else:
        print("Ghost Agent v2.3 - WeChat Account Assistant")
        print()
        article = assistant.write_article("10 Must-Have AI Tools")
        print("Title: " + article["title"])
        print("Tags: " + str(article["tags"]))
        assistant.dashboard()
