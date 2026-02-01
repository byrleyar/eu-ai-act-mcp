# Word Template Mapping Guide

Use these placeholders in your Word document. The system will replace them with the LLM-generated answers.

**Note:** For 'Yes/No' questions, the system will automatically convert 'Yes' to ☑ and 'No' to ☐.

| Placeholder | Question Description |
| --- | --- |
| `{{date_last_updated}}` | What is the date this document was last updated? |
| `{{doc_version_number}}` | What is the version number of this document? |
| `{{legal_name}}` | What is the legal name for the model provider? |
| `{{model_name}}` | What is the official model name? |
| `{{model_authenticity}}` | What is model authenticity? |
| `{{release_date}}` | What is the release date of this document? |
| `{{union_release_date}}` | What is the union release date of this document? |
| `{{model_dependencies}}` | What are the model dependencies? |
| `{{model_architecture}}` | What is the model architecture? |
| `{{design_specs}}` | What are the design specifications of the model? |
| `{{input_modalities_text_check}}` | Did you use text as an input modality? |
| `{{input_modalities_text_max}}` | What is the maximum input size for the text input modality |
| `{{input_modalities_images_check}}` | Did you use images as an input modality? |
| `{{input_modalities_images_max}}` | What is the maximum input size for the images input modality |
| `{{input_modalities_audio_check}}` | Did you use audio as an input modality? |
| `{{input_modalities_audio_max}}` | What is the maximum input size for the audio input modality |
| `{{input_modalities_video_check}}` | Did you use video as an input modality? |
| `{{input_modalities_video_max}}` | What is the maximum input size for the video input modality |
| `{{input_modalities_other_check}}` | Did you use any other input modalities besides text, images, audio, video? |
| `{{input_modalities_other_max}}` | What is the maximum input size for the other input modalities |
| `{{output_modalities_text_check}}` | Did you use text as an output modality? |
| `{{output_modalities_text_max}}` | What is the maximum output size for the text output modality |
| `{{output_modalities_images_check}}` | Did you use images as an output modality? |
| `{{output_modalities_images_max}}` | What is the maximum output size for the images output modality |
| `{{output_modalities_audio_check}}` | Did you use audio as an output modality? |
| `{{output_modalities_audio_max}}` | What is the maximum output size for the audio output modality |
| `{{output_modalities_video_check}}` | Did you use video as an output modality? |
| `{{output_modalities_video_max}}` | What is the maximum output size for the video output modality |
| `{{output_modalities_other_check}}` | Did you use any other output modalities besides text, images, audio, video? |
| `{{output_modalities_other_max}}` | What is the maximum output size for the other output modalities |
| `{{total_model_size}}` | What is the size of the text model? |
| `{{total_model_size_500m}}` | Does the total size of the model fall between 1 and 500M parameters? |
| `{{total_model_size_5b}}` | Does the total size of the model fall between 500M and 5B parameters? |
| `{{total_model_size_15b}}` | Does the total size of the model fall between 5B and 15B parameters? |
| `{{total_model_size_50b}}` | Does the total size of the model fall between 15B and 50B parameters? |
| `{{total_model_size_100b}}` | Does the total size of the model fall between 50B and 100B parameters? |
| `{{total_model_size_500b}}` | Does the total size of the model fall between 100B and 500B parameters? |
| `{{total_model_size_1t}}` | Does the total size of the model fall between 500B and 1T parameters? |
| `{{total_model_size_max}}` | Is the total size of the model greater than 1T parameters? |
| `{{distribution_channels_aio_nca}}` | What are the distribution channels for the model?  This answer will be shared with AIO and NCAs |
| `{{distribution_channels_dps}}` | What are the distribution channels for the model?  This answer will be shared with DPs |
| `{{license_link}}` | What is the link to the license? |
| `{{license_category}}` | What is the license category? |
| `{{license_assets}}` | Are there any additional assets to report? |
| `{{acceptable_use_policy}}` | Please provide a link to the acceptable use policy? |
| `{{intended_uses}}` | Please provide a list of intended uses. |
| `{{type_and_nature}}` | What are the type and nature of AI systems in which the general-purpose AI model can be integrated:? |
| `{{technical_means}}` | What are the technical means for model integration:? |
| `{{required_hardware}}` | What is a description of the required hardware? |
| `{{required_software}}` | What is a description of the required software? |
| `{{design_specifications}}` | What are the design specifications of the training process? |
| `{{decision_rationale}}` | Describe how key decisions were made. |
| `{{data_training_type_text}}` | Was text data used for training, testing, or validation? |
| `{{data_training_type_images}}` | Were images used for training, testing, or validation? |
| `{{data_training_type_audio}}` | Was audio data used for training, testing, or validation? |
| `{{data_training_type_video}}` | Was video data used for training, testing, or validation? |
| `{{data_training_type_other}}` | Was any data besides text, images, audio, or video used for training, testing, or validation? |
| `{{data_provenance_web}}` | Did any data used for training, testing, or validation come from web crawling? |
| `{{data_provenance_private}}` | Did any data used for training, testing, or validation come from Private non-publicly available datasets obtained from third parties? |
| `{{data_provenance_user}}` | Did any data used for training, testing, or validation come from user data? |
| `{{data_provenance_public}}` | Did any data used for training, testing, or validation come from publicly available datasets? |
| `{{data_provenance_synthetic}}` | Did any data used for training, testing, or validation come from Synthetic data that is not publicly accessible (when created directly by or on behalf of the provider)? |
| `{{data_provenance_other_check}}` | Did any data used for training, testing, or validation come from data collected from other means (besides web crawling, private non-publicly available data, user data, publicly available datasets, or synthetic data)? |
| `{{data_provenance_other}}` | Did any data used for training, testing, or validation come from data collected from other means (besides web crawling, private non-publicly available data, user data, publicly available datasets, or synthetic data)? |
| `{{how_data_obtained}}` | How was data obtained and selected? |
| `{{data_points_ncas}}` | How much data was used? This answer will be shared with NCAs |
| `{{data_points_aio}}` | How much data was used? This answer will be shared with AIO |
| `{{scope}}` | What are the scope and main characteristics? |
| `{{data_curation}}` | What are your data curation methodologies? |
| `{{detect_unsuitability}}` | What measures did you take to detect unsuitability of your data sources? |
| `{{detect_biases}}` | What measures did you take to detect unidentifiable biases? |
| `{{training_time_ncas}}` | How long did it take you to train your model? This answer will be shared with NCAs |
| `{{training_time_aio}}` | How long did it take you to train your model? This answer will be shared with AIO |
| `{{computation_used_ncas}}` | What was the amount of computation used for training? This answer will be shared with NCAs |
| `{{computation_used_aio}}` | What was the amount of computation used for training? This answer will be shared with AIO |
| `{{computation_methodology}}` | How did you measure computation used for training? |
| `{{energy_used}}` | How much energy was used for training? |
| `{{energy_methodology}}` | What is your energy measurement methodology? |
| `{{benchmark_computation}}` | What is the benchmarked amount of computation used for inference? This item relates to energy consumption during inference, which makes up the 'energy consumption of the model' (Annex XI, 2(e), AI Act) together with energy consumption during training. Since energy consumption during inference depends on more than just the model itself, the information required for this item is limited to relevant information depending only on the model, namely computational resources used for inference. |
| `{{computation_measurement_methodology}}` | What is the measurement methodology used to calcualte the benchmark computation for inference? |