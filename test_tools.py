"""
각 도구 15개가 올바른 매개변수로 구동하는지 테스트
"""
import sys
sys.path.insert(0, '/home/user/semiprocess_mcp')

from api.index import TOOL_HANDLERS

def test_all_tools():
    """모든 15개 도구 테스트"""
    tests = [
        {
            "name": "analyze_defect",
            "args": {
                "defect_code": "SCRATCH",
                "defect_description": "웨이퍼 가장자리 깊은 스크래치",
                "process_step": "CMP",
                "equipment_id": "CMP-02",
                "wafer_id": "W12345"
            }
        },
        {
            "name": "get_defect_history",
            "args": {
                "defect_type": "SCRATCH",
                "records_csv": "2025-01-10,CMP-01,3,패드교체,해결;2025-01-08,CMP-02,5,필터교체,진행중"
            }
        },
        {
            "name": "suggest_corrective_action",
            "args": {
                "problem_description": "압력 불안정",
                "affected_equipment": "ETCH-01",
                "severity": "critical",
                "current_status": "재시작 후에도 알람 반복 발생"
            }
        },
        {
            "name": "compare_to_baseline",
            "args": {
                "recipe_name": "Oxide Etch",
                "baseline_params": "temperature:60:55:65:C,pressure:30:25:35:mTorr",
                "current_params": "temperature:67,pressure:28"
            }
        },
        {
            "name": "compare_two_recipes",
            "args": {
                "recipe_a_name": "A라인",
                "recipe_a_params": "temperature:60,pressure:30,rf_power:800",
                "recipe_b_name": "B라인",
                "recipe_b_params": "temperature:62,pressure:28,rf_power:820",
                "tolerance_params": "temperature:5%,pressure:10%,rf_power:5%"
            }
        },
        {
            "name": "validate_process_window",
            "args": {
                "process_name": "CVD",
                "window_params": "temperature:450-500,pressure:0.5-1.5",
                "test_params": "temperature:480,pressure:0.8",
                "critical_params": "temperature"
            }
        },
        {
            "name": "analyze_spc_data",
            "args": {
                "parameter_name": "CD",
                "data_points": "45.2,45.8,44.9,46.1,45.5,45.3,45.7,46.0",
                "usl": 50,
                "lsl": 40,
                "target": 45
            }
        },
        {
            "name": "predict_defect_risk",
            "args": {
                "process_name": "Etch",
                "window_params": "temperature:100-130,pressure:50-100",
                "current_params": "temperature:128,pressure:92",
                "severity_params": "temperature:8,pressure:5",
                "critical_params": "temperature"
            }
        },
        {
            "name": "analyze_trend",
            "args": {
                "parameter_name": "Temperature",
                "data_points": "120.1,120.3,120.5,121.2,121.8,122.3",
                "timestamps": "08:00,09:00,10:00,11:00,12:00,13:00",
                "usl": 125,
                "lsl": 120,
                "forecast_count": 3
            }
        },
        {
            "name": "analyze_metrics",
            "args": {
                "period": "2025년 1월 2주차",
                "metrics_data": "yield:97.8,cpk:1.28,uptime:89.5",
                "targets_data": "yield:98,cpk:1.33,uptime:90"
            }
        },
        {
            "name": "generate_shift_report",
            "args": {
                "shift_info": "Day:2025-01-15",
                "production_data": "in:200,out:195,target:200,yield:98.2",
                "equipment_status": "ETCH-01:running:정상;ETCH-02:down:PM중;CVD-01:running:정상",
                "quality_data": "defects:5,major:파티클3건+스크래치2건",
                "events": "14:00 PM시작;16:00 온도경고",
                "pending_actions": "ETCH-02복구확인;온도모니터링"
            }
        },
        {
            "name": "analyze_equipment_comparison",
            "args": {
                "equipment_list": "CMP-01,CMP-02,CMP-03",
                "metrics_data": "CMP-01:yield:98.5,cpk:1.45,uptime:92;CMP-02:yield:97.2,cpk:1.28,uptime:88;CMP-03:yield:98.1,cpk:1.38,uptime:91",
                "weights_csv": "yield:0.4,cpk:0.3,uptime:0.3",
                "benchmark_csv": "yield:98,cpk:1.33,uptime:90"
            }
        },
        {
            "name": "optimize_recipe_direction",
            "args": {
                "recipe_csv": "temperature:450,pressure:1.0,time:300",
                "perf_csv": "thickness:950,uniformity:92,yield:97",
                "target_csv": "thickness:1000,uniformity:95,yield:98"
            }
        },
        {
            "name": "simulate_parameter_change",
            "args": {
                "state_csv": "recipe:temperature:120,time:300,pressure:75;performance:etch_rate:50,uniformity:91,yield:97",
                "changes_csv": "time:250",
                "rules_csv": "time->etch_rate:-10;time->uniformity:-2",
                "window_csv": "temperature:100-140,pressure:50-100"
            }
        },
        {
            "name": "calculate_yield_impact",
            "args": {
                "baseline_yield": 97.5,
                "changes_csv": "temperature:start:65,end:70,sensitivity:0.8;pressure:start:30,end:33,sensitivity:0.1",
                "interactions_csv": "temperature×pressure:-0.2",
                "confidence_level": 0.95,
                "model_type": "linear"
            }
        }
    ]
    
    print("=" * 80)
    print("15개 도구 구동 테스트 시작")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test in tests:
        name = test["name"]
        args = test["args"]
        handler = TOOL_HANDLERS.get(name)
        
        try:
            result = handler(**args)
            if result and isinstance(result, str):
                print(f"✅ {name}: PASS")
                passed += 1
            else:
                print(f"❌ {name}: FAIL (empty result)")
                failed += 1
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            failed += 1
    
    print("=" * 80)
    print(f"결과: {passed} PASS, {failed} FAIL")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = test_all_tools()
    sys.exit(0 if success else 1)
