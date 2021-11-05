def update_pipeline(pipeline):
    """
    Move the pipeline.
    Update the pipeline.
    Create receipts.
    :param pipeline: pipeline at start opf period
    :return: pipeline at end of period and the receipts for the given period.
    """
    for receipt in pipeline:
        receipt["eta"] -= 1

    return pipeline
