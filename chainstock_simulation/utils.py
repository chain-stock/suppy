def update_pipeline(pipeline):
    """
    Move the pipeline.
    Update the pipeline.
    Create receipts.
    :param pipeline: pipeline at start opf period
    :return: pipeline at end of period and the receipts for the given period.
    """
    receipts = []
    for receipt in pipeline:
        receipt["eta"] -= 1
        if receipt["eta"] == 0:
            receipts.append(receipt)

    for receipt in receipts:
        pipeline.remove(receipt)

    return pipeline, receipts
