#!/usr/bin/env python3
"""테스트 실행 스크립트."""
import unittest
import sys
import os

# 프로젝트 루트를 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def run_all_tests():
    """모든 테스트 실행."""
    # 테스트 디렉토리
    test_dir = os.path.join(project_root, 'tests')

    # 테스트 로더
    loader = unittest.TestLoader()

    # 테스트 스위트 생성
    suite = loader.discover(test_dir, pattern='test_*.py')

    # 테스트 러너 (상세 출력)
    runner = unittest.TextTestRunner(verbosity=2)

    # 테스트 실행
    result = runner.run(suite)

    # 결과 요약
    print("\n" + "=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)
    print(f"실행: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"에러: {len(result.errors)}")

    if result.failures:
        print("\n실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\n에러 발생 테스트:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    print("=" * 70)

    # 결과 반환 (CI용)
    return len(result.failures) + len(result.errors) == 0


def run_specific_tests(test_names):
    """특정 테스트만 실행."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for name in test_names:
        try:
            # 모듈 이름으로 로드 시도
            tests = loader.loadTestsFromName(f'tests.{name}')
            suite.addTests(tests)
        except Exception as e:
            print(f"테스트 로드 실패: {name} - {e}")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return len(result.failures) + len(result.errors) == 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 특정 테스트 실행
        # 예: python run_tests.py test_person test_family_tree
        success = run_specific_tests(sys.argv[1:])
    else:
        # 모든 테스트 실행
        success = run_all_tests()

    sys.exit(0 if success else 1)
