import hmac
import hashlib
import urllib.parse
import requests
import uuid
from datetime import datetime, timezone, timedelta
import base64
import logging
import time
import json
import random
import string
import os
from config import load_api_config

logger = logging.getLogger(__name__)
# 关键词列表：移民领域中可能包含偏见或歧视的语言

IMMIGRATION\_BIAS\_KEYWORDS = \[
"deportation", "illegal alien", "go back to your country", "they don't belong here",
"anchor baby", "invasion", "drain our resources", "taking our jobs", "flooding the border",
"criminal immigrants", "foreign threat", "stealing benefits", "build the wall",
"overrun by immigrants", "national security risk", "mass migration crisis", "no assimilation",
"unvetted migrants", "open border disaster", "burden on taxpayers"
]

class IflytekAPI:
    def __init__(self):
        self.api_config = load_api_config()
        self.max_retries = 30  # 增加最大重试次数
        self.retry_delay = 10  # 增加重试延迟时间
        self.query_interval = 100  # 增加查询间隔时间
        self.post_audio_url = "https://audit.iflyaisol.com/audit/v2/audio"
        self.query_url = "https://audit.iflyaisol.com/audit/v2/query"
        
        # 支持的音频格式
        self.supported_formats = ['mp3', 'alaw', 'ulaw', 'pcm', 'aac', 'wav']
        
    def generate_signature(self):
        """Generate signature for iFlytek API"""
        # Get UTC time
        tz = timezone(timedelta())
        fmt = '%Y-%m-%dT%H:%M:%S%z'
        zoned_time = datetime.today().astimezone(tz)
        zoned_time = str(zoned_time.strftime(fmt))
        
        # Prepare parameters
        data_dict = {
            "appId": self.api_config['app_id'],
            "accessKeyId": self.api_config['api_key'],
            "accessKeySecret": self.api_config['api_secret'],
            "utc": zoned_time,
            "uuid": ''.join(random.sample(string.ascii_letters + string.digits, 32))
        }
        
        # Sort parameters
        params_list = sorted(data_dict.items(), key=lambda e: e[0], reverse=False)
        params_str_dict = dict(params_list)
        
        # URL encode parameters
        params_str_urlencode = urllib.parse.urlencode(params_str_dict)
        
        # Generate signature
        base_string = hmac.new(
            self.api_config['api_secret'].encode('utf-8'),
            params_str_urlencode.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        signature = base64.b64encode(base_string).decode('utf-8')
        params_str_dict["signature"] = signature
        
        return params_str_dict
        
    def analyze_audio(self, audio_url):
        """Analyze content using iFlytek Audio Moderation API"""
        # 检查音频格式
        audio_format = None
        # 尝试从URL中提取格式
        if '.' in audio_url:
            audio_format = audio_url.split('.')[-1].lower()
            if audio_format not in self.supported_formats:
                audio_format = None
                
        # 如果无法从URL中获取格式，默认使用mp3
        if audio_format is None:
            logger.warning("无法从URL中获取音频格式，默认使用mp3格式")
            audio_format = 'mp3'
            
        logger.info(f"使用音频格式: {audio_format}")
            
        for attempt in range(self.max_retries):
            try:
                # Generate signature and parameters
                params = self.generate_signature()
                
                # Prepare request headers
                headers = {
                    'Content-Type': 'application/json;charset=UTF-8',
                    'Accept': 'application/json'
                }
                
                # Log request details
                logger.debug(f"Request URL: {self.post_audio_url}")
                logger.debug(f"Request headers: {headers}")
                logger.debug(f"Request params: {params}")
                logger.debug(f"Audio URL: {audio_url}")
                
                # Prepare request data according to official documentation
                data = {
                    "audio_list": [{
                        "audio_type": audio_format,
                        "file_url": audio_url,
                        "name": os.path.basename(audio_url)
                    }],
                    "notify_url": ""  # 暂时不使用回调
                }
                
                # Send request
                response = requests.post(
                    self.post_audio_url,
                    params=params,
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                # Log response details
                logger.debug(f"Response status code: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                logger.debug(f"Response content: {response.text[:500]}...")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get('code') == "000000":  # 成功状态码
                            # Get request_id for querying results
                            request_id = result.get('data', {}).get('request_id')
                            if request_id:
                                return self.query_results(request_id)
                            else:
                                raise Exception("No request_id in response")
                        else:
                            error_message = result.get('desc', result.get('message', 'Unknown error'))
                            error_code = result.get('code', 'Unknown code')
                            
                            if error_code == "100002":
                                logger.warning(f"API Error 100002: {error_message}. Retrying... (Attempt {attempt + 1}/{self.max_retries})")
                                if attempt < self.max_retries - 1:
                                    time.sleep(self.retry_delay)
                                    continue
                            
                            raise Exception(f"API Error {error_code}: {error_message}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse API response: {str(e)}")
                        logger.error(f"Raw response: {response.text}")
                        raise Exception(f"Invalid API response format: {str(e)}")
                else:
                    raise Exception(f"API request failed with status code: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error during API call: {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds... (Attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                    continue
                raise Exception(f"Network error after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                logger.error(f"iFlytek API analysis failed: {str(e)}")
                raise
                
        raise Exception(f"Failed after {self.max_retries} attempts")
        
    def query_results(self, request_id):
        """Query analysis results"""
        start_time = time.time()
        max_wait_time = 3600  # 最大等待时间1小时
        
        for attempt in range(self.max_retries):
            try:
                # 检查是否超过最大等待时间
                elapsed_time = time.time() - start_time
                if elapsed_time > max_wait_time:
                    raise Exception("分析超时，请稍后重试")
                    
                # Generate signature and parameters
                params = self.generate_signature()
                
                # Prepare request headers
                headers = {
                    'Content-Type': 'application/json;charset=UTF-8',
                    'Accept': 'application/json'
                }
                
                # Prepare request data
                data = {
                    "request_id": request_id
                }
                
                # Send query request
                response = requests.post(
                    self.query_url,
                    params=params,
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    code = result.get('code')
                    desc = result.get('desc')
                    sid = result.get('sid')
                    
                    # 记录会话ID，用于排查问题
                    logger.info(f"Session ID: {sid}")
                    
                    if code != "000000":
                        raise Exception(f"API Error {code}: {desc}")
                        
                    data = result.get('data', {})
                    audit_status = data.get('audit_status')
                    
                    if audit_status == 2:  # 审核完成
                        result_list = data.get('result_list', [])
                        if not result_list:
                            return {
                                "status": "success",
                                "message": "未发现违规内容",
                                "suggest": "pass"
                            }
                            
                        # 处理审核结果
                        analysis_results = {
                            "status": "success",
                            "suggest": "pass",  # 默认通过
                            "violations": []
                        }
                        
                        for item in result_list:
                            name = item.get('name')
                            suggest = item.get('suggest')
                            
                            # 更新整体建议
                            if suggest == "block":
                                analysis_results["suggest"] = "block"
                            elif suggest == "review" and analysis_results["suggest"] != "block":
                                analysis_results["suggest"] = "review"
                                
                            detail = item.get('detail', {})
                            audios = detail.get('audios', [])
                            
                            for audio in audios:
                                content = audio.get('content')
                                offset_time = audio.get('offsetTime')
                                duration = audio.get('duration')
                                audio_url = audio.get('audio_url')
                                audio_suggest = audio.get('suggest')
                                
                                # 处理分类结果
                                categories = []
                                for category in audio.get('category_list', []):
                                    category_info = {
                                        "description": category.get('category_description'),
                                        "suggest": category.get('suggest'),
                                        "words": category.get('word_list', [])
                                    }
                                    categories.append(category_info)
                                    
                                # 只记录需要关注的内容
                                if audio_suggest != "pass":
                                    analysis_results["violations"].append({
                                        "name": name,
                                        "content": content,
                                        "offset_time": offset_time,
                                        "duration": duration,
                                        "audio_url": audio_url,
                                        "suggest": audio_suggest,
                                        "categories": categories
                                    })
                                    
                        return analysis_results
                        
                    elif audit_status == 4:  # 审核异常
                        raise Exception(f"审核异常: {data.get('message', 'Unknown error')}")
                    else:  # 待审核或审核中
                        # 计算进度百分比
                        progress = min(100, int((elapsed_time / max_wait_time) * 100))
                        status_text = "待审核" if audit_status == 0 else "审核中"
                        logger.info(f"{status_text} (进度: {progress}%, 已用时间: {int(elapsed_time)}秒)")
                        
                        # 根据进度调整查询间隔
                        if progress < 30:
                            time.sleep(self.query_interval)
                        elif progress < 60:
                            time.sleep(self.query_interval * 2)
                        else:
                            time.sleep(self.query_interval * 3)
                        continue
                else:
                    raise Exception(f"请求失败，状态码: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"查询失败: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
                
        raise Exception(f"查询失败，已达到最大重试次数: {self.max_retries}") 
