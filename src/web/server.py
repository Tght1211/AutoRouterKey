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
CORS(app)

DATA_DIR = Path("data")
RESULTS_DIR = DATA_DIR / "results"
ACCOUNTS_JSON = DATA_DIR / "accounts.json"
KEY_HISTORY_JSON = DATA_DIR / "key_history.json"



def ensure_data_dir():
    """确保 data 目录存在"""
    DATA_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

def load_accounts_from_json():
    """从JSON文件加载所有账号数据"""
    if not ACCOUNTS_JSON.exists():
        return []
    
    try:
        with open(ACCOUNTS_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('accounts', [])
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return []



def save_accounts_to_json(accounts):
    """保存账号数据到JSON文件"""
    try:
        data = {'accounts': accounts}
        with open(ACCOUNTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存账号数据失败: {e}")
        return False



@app.route('/')
def index():
    """返回主页面"""
    return send_from_directory('templates', 'manager.html')

@app.route('/api/accounts')
def get_accounts():
    """获取所有账号"""
    try:
        # 从JSON文件加载所有账号
        accounts = load_accounts_from_json()
        
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
        
        # 从JSON文件加载账号
        accounts = load_accounts_from_json()
        target_account = None
        
        for account in accounts:
            if str(account['id']) == str(account_id):
                target_account = account
                break
        
        if not target_account:
            return jsonify({
                'success': False,
                'error': '账号不存在'
            }), 404
        
        # 更新账号状态
        target_account['status'] = new_status
        target_account['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存到JSON文件
        if save_accounts_to_json(accounts):
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
        
        # 从JSON文件加载账号
        accounts = load_accounts_from_json()
        target_account = None
        
        for account in accounts:
            if str(account['id']) == str(account_id):
                target_account = account
                break
        
        if not target_account:
            return jsonify({
                'success': False,
                'error': '账号不存在'
            }), 404
        
        # 更新OpenRouter状态
        target_account['openrouter'] = openrouter_status
        target_account['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存到JSON文件
        if save_accounts_to_json(accounts):
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
        
        # 从JSON文件加载账号
        accounts = load_accounts_from_json()
        target_account = None
        
        for account in accounts:
            if str(account['id']) == str(account_id):
                target_account = account
                break
        
        if not target_account:
            return jsonify({
                'success': False,
                'error': '账号不存在'
            }), 404
        
        # 更新备注
        target_account['notes'] = notes
        target_account['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存到JSON文件
        if save_accounts_to_json(accounts):
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
        accounts = load_accounts_from_json()
        today = datetime.now().strftime('%Y-%m-%d')
        key_history = _load_key_history()

        total = len(accounts)
        available = len([a for a in accounts if a.get('status') == 'available'])
        registered = len([a for a in accounts if a.get('openrouter')])
        has_api_key = len([a for a in accounts if a.get('openrouter_api_key')])
        used = len([a for a in accounts if a.get('status') == 'used'])
        today_keys = len([k for k in key_history if k.get('date') == today])

        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'available': available,
                'registered': registered,
                'has_api_key': has_api_key,
                'used': used,
                'today_keys': today_keys
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _load_key_history():
    """加载 Key 历史记录"""
    try:
        if KEY_HISTORY_JSON.exists():
            with open(KEY_HISTORY_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []


@app.route('/api/keys/daily')
def get_daily_keys():
    """按日期分组返回 Key 诞生记录"""
    try:
        history = _load_key_history()
        daily = {}
        for k in history:
            d = k.get('date', 'unknown')
            daily.setdefault(d, []).append(k)
        # 按日期倒序
        sorted_daily = sorted(daily.items(), key=lambda x: x[0], reverse=True)
        return jsonify({
            'success': True,
            'data': [{'date': d, 'keys': keys, 'count': len(keys)} for d, keys in sorted_daily]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/keys/today')
def get_today_keys():
    """返回今日诞生的 Key 列表"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        history = _load_key_history()
        today_keys = [k for k in history if k.get('date') == today]
        return jsonify({
            'success': True,
            'date': today,
            'data': today_keys,
            'count': len(today_keys)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/api/accounts/refresh', methods=['POST'])
def refresh_accounts():
    """刷新账号数据"""
    try:
        # 检查accounts.json文件修改时间
        accounts_file_info = {}
        
        if ACCOUNTS_JSON.exists():
            stat = ACCOUNTS_JSON.stat()
            accounts_file_info = {
                'exists': True,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            accounts_file_info = {
                'exists': False,
                'size': 0,
                'modified': ''
            }
        
        # 重新加载账号数据
        accounts = load_accounts_from_json()
        
        return jsonify({
            'success': True,
            'file_info': accounts_file_info,
            'total_accounts': len(accounts),
            'message': '账号数据刷新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



if __name__ == '__main__':
    ensure_data_dir()
    print("🚀 AutoRouterKey Web 管理平台启动中...")
    print("📍 Web界面: http://localhost:5010")
    print("📍 API文档: http://localhost:5010/api/accounts")
    print("🔄 支持热重载，修改文件后会自动更新")
    
    app.run(host='0.0.0.0', port=5010, debug=True)
