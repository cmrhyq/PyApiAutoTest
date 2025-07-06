#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@File send_email.py
@Contact cmrhyq@163.com
@License (C)Copyright 2022-2025, AlanHuang
@Modify Time 2024/6/25 23:28
@Author Alan Huang
@Version 0.0.1
@Description None
"""
import mimetypes
from pathlib import Path
from typing import List, Union
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.header import Header
from smtplib import SMTP, SMTP_SSL
from common.log import Logger
from core.config.ini.read_config_ini import ReadConfigIni

logger = Logger().get_logger()


class SendEmail:
    """邮件发送类"""
    
    def __init__(self, use_ssl: bool = True):
        """
        初始化邮件发送类
        :param host: SMTP服务器地址
        :param port: SMTP服务器端口
        :param sender: 发件人邮箱
        :param password: 邮箱授权码
        :param use_ssl: 是否使用SSL连接，默认True
        """
        self.conf = ReadConfigIni()
        self.host = self.conf.mail_host
        self.port = self.conf.mail_port
        self.sender = self.conf.mail_sender
        self.password = self.conf.mail_license
        self.use_ssl = use_ssl
        self.smtp = SMTP_SSL(self.host, self.port) if use_ssl else SMTP(self.host, self.port)
        self.message = MIMEMultipart('alternative')
        self._init_message()

    def _init_message(self):
        """初始化邮件基本信息"""
        self.message['From'] = self._format_address(self.sender)
        self.message.preamble = 'You need a MIME-aware mail reader to see this message.'

    def _format_address(self, address: str) -> str:
        """格式化邮件地址"""
        if '@' not in address:
            raise ValueError(f"Invalid email address: {address}")
        name, addr = address.split('@')
        return f"{name}<{address}>"

    def _get_mime_type(self, filepath: str) -> str:
        """获取文件MIME类型"""
        return mimetypes.guess_type(filepath)[0] or 'application/octet-stream'

    def set_receivers(self, receivers: Union[str, List[str]]):
        """设置收件人"""
        if isinstance(receivers, str):
            receivers = [receivers]
        self.message['To'] = ','.join(self._format_address(r) for r in receivers)
        self.receivers = receivers
        return self

    def set_subject(self, subject: str):
        """设置邮件主题"""
        self.message['Subject'] = Header(subject, 'utf-8')
        return self

    def set_content(self, content: str, content_type: str = 'plain'):
        """
        设置邮件内容
        :param content: 邮件内容
        :param content_type: 内容类型，'plain' 或 'html'
        """
        self.message.attach(MIMEText(content, content_type, 'utf-8'))
        return self

    def add_attachment(self, filepath: Union[str, Path]):
        """
        添加附件
        :param filepath: 文件路径
        """
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                logger.error(f"附件不存在: {filepath}")
                return self

            mime_type = self._get_mime_type(str(filepath))
            with open(filepath, 'rb') as f:
                data = f.read()

            if mime_type.startswith('image/'):
                attachment = MIMEImage(data)
            elif mime_type.startswith('audio/'):
                attachment = MIMEAudio(data)
            else:
                attachment = MIMEApplication(data)

            attachment.add_header('Content-Disposition', 'attachment', 
                                filename=filepath.name)
            self.message.attach(attachment)
            logger.info(f"成功添加附件: {filepath.name}")
        except Exception as e:
            logger.error(f"添加附件失败: {str(e)}")
        return self

    def send(self) -> bool:
        """
        发送邮件
        :return: 是否发送成功
        """
        try:
            logger.info("开始发送邮件...")
            self.smtp.ehlo()
            if not self.use_ssl:
                self.smtp.starttls()
            self.smtp.login(self.sender, self.password)
            self.smtp.send_message(self.message)
            logger.info("邮件发送成功")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False
        finally:
            try:
                self.smtp.quit()
            except Exception:
                pass


if __name__ == '__main__':
    # 示例用法
    email = SendEmail()
    
    email.set_receivers(["1678336204@qq.com"]) \
        .set_subject("测试邮件") \
        .set_content("<h1>这是一封测试邮件</h1>", "html") \
        .add_attachment("../../resource/img/cat.png") \
        .send()
