from kubernetes import client, config
import time
import json
import os

# Load Kubernetes config
try:
    config.load_kube_config()
except:
    config.load_incluster_config()

batch_v1 = client.BatchV1Api()
core_v1 = client.CoreV1Api()

def collect_all_job_results():
    """Collect results from all Maven build jobs"""
    
    # Wait for jobs to complete
    print("⏳ Waiting for all jobs to complete...")
    max_wait = 600  # 10 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        jobs = batch_v1.list_namespaced_job(namespace="default")
        
        completed_jobs = 0
        failed_jobs = 0
        running_jobs = 0
        
        for job in jobs.items:
            if job.metadata.name.startswith("test-"):
                if job.status.succeeded:
                    completed_jobs += 1
                elif job.status.failed:
                    failed_jobs += 1
                else:
                    running_jobs += 1
        
        total_jobs = completed_jobs + failed_jobs + running_jobs
        print(f"📊 Jobs status: {completed_jobs} completed, {failed_jobs} failed, {running_jobs} running (Total: {total_jobs})")
        
        if running_jobs == 0:
            print("✅ All jobs completed!")
            break
            
        time.sleep(10)
    
    # Collect logs from all jobs
    results = []
    jobs = batch_v1.list_namespaced_job(namespace="default")
    
    for job in jobs.items:
        if job.metadata.name.startswith("test-"):
            job_name = job.metadata.name
            repo_name = job.metadata.labels.get('repo', 'unknown')
            
            # Get pods for this job
            pods = core_v1.list_namespaced_pod(
                namespace="default",
                label_selector=f"job-name={job_name}"
            )
            
            job_result = {
                'job_name': job_name,
                'repo_name': repo_name,
                'status': 'unknown',
                'duration': 0,
                'logs': '',
                'success': False
            }
            
            if pods.items:
                pod = pods.items[0]
                
                # Get job status
                if job.status.succeeded:
                    job_result['status'] = 'succeeded'
                    job_result['success'] = True
                elif job.status.failed:
                    job_result['status'] = 'failed'
                else:
                    job_result['status'] = 'running'
                
                # Calculate duration
                if job.status.start_time and job.status.completion_time:
                    duration = (job.status.completion_time - job.status.start_time).total_seconds()
                    job_result['duration'] = duration
                
                # Get logs
                try:
                    logs = core_v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace="default"
                    )
                    job_result['logs'] = logs
                    
                    # Check if Maven build was successful
                    if "BUILD SUCCESS" in logs:
                        job_result['maven_success'] = True
                    elif "BUILD FAILURE" in logs:
                        job_result['maven_success'] = False
                    else:
                        job_result['maven_success'] = None
                        
                except Exception as e:
                    job_result['logs'] = f"Failed to get logs: {str(e)}"
            
            results.append(job_result)
            print(f"📋 Collected results for {repo_name}: {job_result['status']}")
    
    return results

def generate_report(results):
    """Generate a comprehensive report"""
    
    total_jobs = len(results)
    successful_jobs = len([r for r in results if r['success']])
    failed_jobs = total_jobs - successful_jobs
    
    maven_success = len([r for r in results if r.get('maven_success') == True])
    maven_failed = len([r for r in results if r.get('maven_success') == False])
    maven_unknown = len([r for r in results if r.get('maven_success') is None])
    
    total_duration = sum([r['duration'] for r in results if r['duration'] > 0])
    avg_duration = total_duration / len([r for r in results if r['duration'] > 0]) if results else 0
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'total_repositories': total_jobs,
            'kubernetes_jobs_successful': successful_jobs,
            'kubernetes_jobs_failed': failed_jobs,
            'maven_builds_successful': maven_success,
            'maven_builds_failed': maven_failed,
            'maven_builds_unknown': maven_unknown,
            'total_build_time_seconds': total_duration,
            'average_build_time_seconds': avg_duration
        },
        'detailed_results': results
    }
    
    return report

# Main execution
if __name__ == "__main__":
    print("🔍 Collecting all Maven build results...")
    results = collect_all_job_results()
    
    print("📊 Generating report...")
    report = generate_report(results)
    
    # Save detailed report
    with open('/workspace/build_results.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Save summary report
    summary_text = f"""
=== MAVEN BUILD RESULTS SUMMARY ===
Timestamp: {report['timestamp']}

📊 OVERALL STATISTICS:
- Total Repositories: {report['summary']['total_repositories']}
- Kubernetes Jobs Successful: {report['summary']['kubernetes_jobs_successful']}
- Kubernetes Jobs Failed: {report['summary']['kubernetes_jobs_failed']}

🔨 MAVEN BUILD RESULTS:
- Successful Builds: {report['summary']['maven_builds_successful']}
- Failed Builds: {report['summary']['maven_builds_failed']}
- Unknown Status: {report['summary']['maven_builds_unknown']}

⏱️ TIMING:
- Total Build Time: {report['summary']['total_build_time_seconds']:.2f} seconds
- Average Build Time: {report['summary']['average_build_time_seconds']:.2f} seconds

🔍 DETAILED RESULTS:
"""
    
    for result in results:
        maven_status = "✅ SUCCESS" if result.get('maven_success') == True else "❌ FAILED" if result.get('maven_success') == False else "❓ UNKNOWN"
        summary_text += f"- {result['repo_name']}: {maven_status} ({result['duration']:.1f}s)\n"
    
    with open('/workspace/build_summary.txt', 'w') as f:
        f.write(summary_text)
    
    print("✅ Results saved to:")
    print("  📄 /workspace/build_results.json (detailed)")
    print("  📄 /workspace/build_summary.txt (summary)")
    print(f"\n📊 QUICK SUMMARY:")
    print(f"  Maven Builds: {report['summary']['maven_builds_successful']}/{report['summary']['total_repositories']} successful")
    print(f"  Total Time: {report['summary']['total_build_time_seconds']:.2f} seconds")
