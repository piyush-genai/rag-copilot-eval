# PURPOSE: Runs RAGAS evaluation (context_precision, faithfulness, answer_relevancy) on the golden test set
# CALLED BY: evaluation.regression_gate, CI/CD pipeline
# DEPENDS ON: ragas, langchain, evaluation.golden_dataset, gateway.query_handler
