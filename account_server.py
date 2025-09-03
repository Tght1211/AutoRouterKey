#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
RESULTS_DIR = Path("Results")
ACCOUNTS_JSON = RESULTS_DIR / "accounts_data.json"

def ensure_results_dir():
    """确保 Results 目录存在"""
    RESULTS_DIR.mkdir(exist_ok=True)

def read_email_file(filename):
    """读取邮箱文件"""
    file_path = RESULTS_DIR / filename
    accounts = []
    
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and ':' in line:
                        try:
                            email, password = line.split(':', 1)
                            accounts.append({
                                'id': line_num,
                                'email': email.strip(),
                                'password': password.strip(),
                                'source_file': filename,
                                'line_number': line_num
                            })
                        except ValueError:
                            print(f"警告: 第{line_num}行格式错误: {line}")
        except Exception as e:
            print(f"读取文件 {filename} 时出错: {e}")
    
    return accounts

def load_accounts_metadata():
    """加载账号元数据（状态、标记等）"""
    if ACCOUNTS_JSON.exists():
        try:
            with open(ACCOUNTS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载账号元数据失败: {e}")
    return {}

def save_accounts_metadata(metadata):
    """保存账号元数据"""
    try:
        with open(ACCOUNTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存账号元数据失败: {e}")
        return False

def merge_account_data(accounts, metadata):
    """合并账号数据和元数据"""
    result = []
    
    for account in accounts:
        email = account['email']
        account_key = f"{email}:{account['password']}"
        
        # 从元数据中获取额外信息
        extra_data = metadata.get(account_key, {})
        
        merged = {
            'id': account['id'],
            'email': email,
            'password': account['password'],
            'status': extra_data.get('status', 'available'),
            'openrouter': extra_data.get('openrouter', False),
            'notes': extra_data.get('notes', ''),
            'created_at': extra_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'last_used': extra_data.get('last_used', ''),
            'source_file': account['source_file'],
            'line_number': account['line_number']
        }
        result.append(merged)
    
    return result

@app.route('/')
def index():
    """返回主页面"""
    return send_from_directory('.', 'account_manager.html')

@app.route('/api/accounts')
def get_accounts():
    """获取所有账号"""
    try:
        # 读取未登录账号
        unlogged_accounts = read_email_file('unlogged_email.txt')
        # 读取已登录账号
        logged_accounts = read_email_file('logged_email.txt')
        
        # 合并所有账号
        all_accounts = unlogged_accounts + logged_accounts
        
        # 读取元数据
        metadata = load_accounts_metadata()
        
        # 合并数据
        accounts = merge_account_data(all_accounts, metadata)
        
        return jsonify({
            'success': True,
            'data': accounts,
            'total': len(accounts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/accounts/<account_id>/status', methods=['PUT'])
def update_account_status(account_id):
    """更新账号状态"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['available', 'registered', 'used']:
            return jsonify({
                'success': False,
                'error': '无效的状态值'
            }), 400
        
        # 找到对应账号
        all_accounts = read_email_file('unlogged_email.txt') + read_email_file('logged_email.txt')
        target_account = None
        
        for account in all_accounts:
            if str(account['id']) == str(account_id):
                target_account = account
                break
        
        if not target_account:
            return jsonify({
                'success': False,
                'error': '账号不存在'
            }), 404
        
        # 更新元数据
        metadata = load_accounts_metadata()
        account_key = f"{target_account['email']}:{target_account['password']}"
        
        if account_key not in metadata:
            metadata[account_key] = {}
        
        metadata[account_key]['status'] = new_status
        metadata[account_key]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if save_accounts_metadata(metadata):
            return jsonify({
                'success': True,
                'message': '状态更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '保存失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/accounts/<account_id>/openrouter', methods=['PUT'])
def update_openrouter_status(account_id):
    """更新 OpenRouter 注册状态"""
    try:
        data = request.get_json()
        openrouter_status = data.get('openrouter', False)
        
        # 找到对应账号
        all_accounts = read_email_file('unlogged_email.txt') + read_email_file('logged_email.txt')
        target_account = None
        
        for account in all_accounts:
            if str(account['id']) == str(account_id):
                target_account = account
                break
        
        if not target_account:
            return jsonify({
                'success': False,
                'error': '账号不存在'
            }), 404
        
        # 更新元数据
        metadata = load_accounts_metadata()
        account_key = f"{target_account['email']}:{target_account['password']}"
        
        if account_key not in metadata:
            metadata[account_key] = {}
        
        metadata[account_key]['openrouter'] = openrouter_status
        metadata[account_key]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if save_accounts_metadata(metadata):
            return jsonify({
                'success': True,
                'message': 'OpenRouter状态更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '保存失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/accounts/<account_id>/notes', methods=['PUT'])
def update_account_notes(account_id):
    """更新账号备注"""
    try:
        data = request.get_json()
        notes = data.get('notes', '')
        
        # 找到对应账号
        all_accounts = read_email_file('unlogged_email.txt') + read_email_file('logged_email.txt')
        target_account = None
        
        for account in all_accounts:
            if str(account['id']) == str(account_id):
                target_account = account
                break
        
        if not target_account:
            return jsonify({
                'success': False,
                'error': '账号不存在'
            }), 404
        
        # 更新元数据
        metadata = load_accounts_metadata()
        account_key = f"{target_account['email']}:{target_account['password']}"
        
        if account_key not in metadata:
            metadata[account_key] = {}
        
        metadata[account_key]['notes'] = notes
        metadata[account_key]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if save_accounts_metadata(metadata):
            return jsonify({
                'success': True,
                'message': '备注更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '保存失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/accounts/stats')
def get_accounts_stats():
    """获取账号统计信息"""
    try:
        # 获取所有账号
        response = get_accounts()
        if response.status_code != 200:
            return response
        
        accounts_data = response.get_json()
        accounts = accounts_data['data']
        
        # 计算统计信息
        total = len(accounts)
        available = len([a for a in accounts if a['status'] == 'available'])
        registered = len([a for a in accounts if a['openrouter']])
        used = len([a for a in accounts if a['status'] == 'used'])
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'available': available,
                'registered': registered,
                'used': used
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/accounts/export')
def export_accounts():
    """导出账号数据"""
    try:
        # 获取所有账号
        response = get_accounts()
        if response.status_code != 200:
            return response
        
        accounts_data = response.get_json()
        accounts = accounts_data['data']
        
        # 生成导出文本
        export_lines = []
        for account in accounts:
            line = f"{account['email']}: {account['password']}"
            if account['status'] != 'available':
                line += f" # {account['status']}"
            if account['openrouter']:
                line += " # OpenRouter已注册"
            if account['notes']:
                line += f" # {account['notes']}"
            export_lines.append(line)
        
        export_text = '\n'.join(export_lines)
        
        return jsonify({
            'success': True,
            'data': export_text,
            'filename': f"outlook_accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/refresh', methods=['POST'])
def refresh_files():
    """刷新文件数据"""
    try:
        # 检查文件修改时间
        file_info = {}
        
        for filename in ['unlogged_email.txt', 'logged_email.txt']:
            file_path = RESULTS_DIR / filename
            if file_path.exists():
                stat = file_path.stat()
                file_info[filename] = {
                    'exists': True,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                file_info[filename] = {
                    'exists': False,
                    'size': 0,
                    'modified': ''
                }
        
        return jsonify({
            'success': True,
            'files': file_info,
            'message': '文件信息刷新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    ensure_results_dir()
    print("🚀 Outlook 账号管理服务器启动中...")
    print("📍 Web界面: http://localhost:5000")
    print("📍 API文档: http://localhost:5000/api/accounts")
    print("🔄 支持热重载，修改文件后会自动更新")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
