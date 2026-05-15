from quanscient.experimental.multiphysicsai import train_surrogate_model

train_surrogate_model(
  value_dataset_names=["training_data"],
  inputs=["x", "y"],
  outputs=["f1", "f2"],
  model_file_name="model.ts",
  epochs=int(expr.epochs),
  hidden_layer_size=int(expr.hidden_layer_size),
  num_blocks=int(expr.num_blocks),
)
