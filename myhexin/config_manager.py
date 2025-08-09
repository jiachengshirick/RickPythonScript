# config_loader.py - 配置加载器
import openai
import yaml
import json
import os
from typing import Dict, Any, Optional
import logging
from pathlib import Path


class ConfigLoader:
    """配置文件加载器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = {}
        self._load_config()
        self._setup_logging()

    def _load_config(self):
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                self._create_default_config()

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            # 处理环境变量
            self._process_environment_variables()

            print(f"配置文件已加载: {self.config_path}")

        except Exception as e:
            raise Exception(f"配置文件加载失败: {e}")

    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            'api_keys': {
                'openai_api_key': '',
                'reddit_client_id': '',
                'reddit_client_secret': '',
                'flux_api_key': '',
                'firefly_api_key': ''
            },
            'image_generation': {
                'provider': 'gpt5'
            },
            'reddit': {
                'user_agent': 'NewsCommentBot/1.0',
                'search_limit': 10
            }
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

        print(f"已创建默认配置文件: {self.config_path}")
        print("请编辑配置文件并填入您的API密钥")

    def _process_environment_variables(self):
        """处理环境变量"""
        env_mapping = {
            'OPENAI_API_KEY': ['api_keys', 'openai_api_key'],
            'REDDIT_CLIENT_ID': ['api_keys', 'reddit_client_id'],
            'REDDIT_CLIENT_SECRET': ['api_keys', 'reddit_client_secret'],
            'FLUX_API_KEY': ['api_keys', 'flux_api_key'],
            'FIREFLY_API_KEY': ['api_keys', 'firefly_api_key']
        }

        for env_key, config_path in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value:
                self._set_nested_value(self.config, config_path, env_value)

    def _set_nested_value(self, config: Dict, path: list, value: Any):
        """设置嵌套字典值"""
        for key in path[:-1]:
            config = config.setdefault(key, {})
        config[path[-1]] = value

    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))

        # 创建日志目录
        log_file = log_config.get('file', './logs/news_bot.log')
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值，支持点号分割的路径"""
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def get_api_key(self, service: str) -> Optional[str]:
        """获取API密钥"""
        key = self.get(f'api_keys.{service}_api_key')
        if not key or key.startswith('your_') or key == '':
            return None
        return key

    def validate_config(self) -> Dict[str, list]:
        """验证配置完整性"""
        errors = {
            'missing_keys': [],
            'invalid_values': [],
            'warnings': []
        }

        # 检查必需的API密钥
        required_keys = ['openai_api_key']
        for key in required_keys:
            if not self.get_api_key(key.replace('_api_key', '')):
                errors['missing_keys'].append(f'api_keys.{key}')

        # 检查图片生成器配置
        provider = self.get('image_generation.provider')
        if provider not in ['gpt5', 'dalle', 'flux', 'firefly', 'local']:
            errors['invalid_values'].append(f'image_generation.provider: {provider}')

        # 检查Reddit配置（可选）
        reddit_id = self.get('api_keys.reddit_client_id')
        reddit_secret = self.get('api_keys.reddit_client_secret')
        if not reddit_id or not reddit_secret:
            errors['warnings'].append('Reddit API未配置，将跳过Reddit评论分析')

        return errors

    def save_user_inputs(self, inputs: Dict[str, Any]):
        """保存用户输入到配置文件"""
        user_config_path = "user_config.json"

        try:
            # 加载现有用户配置
            if os.path.exists(user_config_path):
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
            else:
                user_config = {}

            # 更新配置
            user_config.update(inputs)

            # 保存配置
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(user_config, f, ensure_ascii=False, indent=2)

            print(f"用户配置已保存到: {user_config_path}")

        except Exception as e:
            print(f"保存用户配置失败: {e}")

    def load_user_inputs(self) -> Dict[str, Any]:
        """加载用户输入配置"""
        user_config_path = "user_config.json"

        try:
            if os.path.exists(user_config_path):
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载用户配置失败: {e}")

        return {}


# config_manager.py - 配置管理器
class ConfigManager:
    """配置管理器 - 提供友好的配置接口"""

    def __init__(self, config_path: str = "config.yaml"):
        self.loader = ConfigLoader(config_path)

    def setup_interactive(self):
        """交互式配置设置"""
        print("=== 新闻评论生成器配置向导 ===\n")

        # 加载已有配置
        user_inputs = self.loader.load_user_inputs()

        inputs = {}

        # API密钥配置
        print("1. API密钥配置")
        inputs['openai_api_key'] = self._get_input(
            "请输入OpenAI API密钥",
            user_inputs.get('openai_api_key', ''),
            required=True
        )

        inputs['reddit_client_id'] = self._get_input(
            "请输入Reddit Client ID (可选，按回车跳过)",
            user_inputs.get('reddit_client_id', '')
        )

        if inputs['reddit_client_id']:
            inputs['reddit_client_secret'] = self._get_input(
                "请输入Reddit Client Secret",
                user_inputs.get('reddit_client_secret', '')
            )

        # 图片生成器选择
        print("\n2. 图片生成器选择")
        providers = {
            '1': 'gpt5',
            '2': 'dalle',
            '3': 'flux',
            '4': 'firefly'
        }

        print("可选的图片生成器:")
        print("1. GPT-5 (推荐)")
        print("2. DALL-E 3 (稳定可靠)")
        print("3. Flux (开源，高质量)")
        print("4. Adobe Firefly (商用安全)")

        provider_choice = input(f"请选择 (1-4，默认: 1): ").strip() or '1'
        inputs['image_provider'] = providers.get(provider_choice, 'dalle')

        # 根据选择请求相应API密钥
        if inputs['image_provider'] == 'flux':
            inputs['flux_api_key'] = self._get_input(
                "请输入Flux API密钥",
                user_inputs.get('flux_api_key', '')
            )
        elif inputs['image_provider'] == 'firefly':
            inputs['firefly_api_key'] = self._get_input(
                "请输入Adobe Firefly API密钥",
                user_inputs.get('firefly_api_key', '')
            )

        # 输出设置
        print("\n3. 输出设置")
        inputs['output_directory'] = self._get_input(
            "输出目录路径",
            user_inputs.get('output_directory', './output')
        )

        inputs['export_images'] = self._get_bool_input(
            "是否导出生成的图片?",
            user_inputs.get('export_images', True)
        )

        # 保存配置
        self.loader.save_user_inputs(inputs)

        print(f"\n✅ 配置完成！")
        return inputs

    def _get_input(self, prompt: str, default: str = '', required: bool = False) -> str:
        """获取用户输入"""
        if default:
            display_default = f" (当前: {default[:20]}{'...' if len(default) > 20 else ''})"
        else:
            display_default = ""

        while True:
            value = input(f"{prompt}{display_default}: ").strip()

            if not value and default:
                return default

            if not value and required:
                print("该项为必填项，请输入有效值")
                continue

            return value

    def _get_bool_input(self, prompt: str, default: bool = True) -> bool:
        """获取布尔值输入"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{prompt} ({default_str}): ").strip().lower()

        if not response:
            return default

        return response in ['y', 'yes', 'true', '1']

    def get_runtime_config(self, user_inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        if user_inputs is None:
            user_inputs = self.loader.load_user_inputs()

        # 先从用户交互存储里拿，没有再到 api_keys 里读
        openai_key = (
                user_inputs.get('openai_api_key')
                or self.loader.get_api_key('openai')
        )

        reddit_id = (
                user_inputs.get('reddit_client_id')
                or self.loader.get('api_keys.reddit_client_id')
        )
        reddit_secret = (
                user_inputs.get('reddit_client_secret')
                or self.loader.get('api_keys.reddit_client_secret')
        )

        config = {
            'openai_api_key': openai_key,
            'reddit_client_id': reddit_id,
            'reddit_client_secret': reddit_secret,
            'reddit_user_agent': user_inputs.get('reddit_user_agent')
                                 or self.loader.get('reddit.user_agent'),

            # 其余不变……
            'image_provider': user_inputs.get('image_provider')
                              or self.loader.get('image_generation.provider'),
            'flux_api_key': user_inputs.get('flux_api_key')
                            or self.loader.get_api_key('flux'),
            'firefly_api_key': user_inputs.get('firefly_api_key')
                               or self.loader.get_api_key('firefly'),
            'output_directory': user_inputs.get('output_directory')
                                or self.loader.get('output.output_directory'),
            'export_images': user_inputs.get('export_images')
                             or self.loader.get('output.export_images'),
            'content_analysis': self.loader.get('content_analysis', {}),
            'comment_generation': self.loader.get('comment_generation', {}),
            'image_generation': self.loader.get('image_generation', {}),
            'performance': self.loader.get('performance', {}),
        }

        return config

    def validate_and_setup(self) -> Dict[str, Any]:
        """验证配置并设置"""
        # 检查配置完整性
        errors = self.loader.validate_config()

        if errors['missing_keys'] or errors['invalid_values']:
            print("⚠️  配置验证失败:")

            for key in errors['missing_keys']:
                print(f"  缺少必需配置: {key}")

            for error in errors['invalid_values']:
                print(f"  无效配置: {error}")

            print("\n正在启动配置向导...")
            user_inputs = self.setup_interactive()
            config = self.get_runtime_config(user_inputs)
            os.environ['OPENAI_API_KEY'] = config['openai_api_key']
            openai.api_key = config['openai_api_key']
            return config

        else:
            # 显示警告
            for warning in errors['warnings']:
                print(f"⚠️  {warning}")

            print("✅ 配置验证通过")
            config = self.get_runtime_config()
            os.environ['OPENAI_API_KEY'] = config['openai_api_key']
            openai.api_key = config['openai_api_key']
            return config

if __name__ == "__main__":
    # 测试配置系统
    manager = ConfigManager()
    config = manager.validate_and_setup()
    print(f"\n最终配置预览:")
    print(f"图片生成器: {config['image_provider']}")
    print(f"输出目录: {config['output_directory']}")
    print(f"Reddit集成: {'是' if config['reddit_client_id'] else '否'}")