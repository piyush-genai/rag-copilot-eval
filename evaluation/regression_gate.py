# PURPOSE: Lambda handler that compares current RAGAS scores to baseline and blocks deploy if >5% drop
# CALLED BY: AWS Lambda (CI/CD deployment pipeline step)
# DEPENDS ON: evaluation.ragas_pipeline, boto3 (S3 for baseline scores), AWS CodePipeline approval API
