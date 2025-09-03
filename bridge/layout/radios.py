import re
from os.path import join, abspath, dirname

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html, Input, Output, State

# TODO: Not sure why using this
from bridge.layout.app_layout import CURRENT_DATADICC


class Radios:

    @staticmethod
    def register_callbacks(app):

        @app.callback(
            Output('row2_options', 'children'),
            [Input('row1_radios', 'value')]
        )
        def update_row2_options(selected_value):
            if selected_value == "Characterisation":
                options = [
                    {"label": "What are the case defining features?", "value": "CD_Features"},
                    {"label": "What is the spectrum of clinical features in this disease?",
                     "value": "Spectrum_Clinical_Features"},
                ]
            elif selected_value == "Risk/Prognosis":
                options = [
                    {"label": "What are the clinical features occurring in those with patient outcome?",
                     "value": "Clinical_Features_Patient_Outcome"},
                    {"label": "What are the risk factors for patient outcome?",
                     "value": "Risk_Factors_Patient_Outcome"},
                ]
            elif selected_value == "Clinical Management":
                options = [
                    {"label": "What treatment/intervention are received by those with patient outcome?",
                     "value": "Treatment_Intervention_Patient_Outcome"},
                    {"label": "What proportion of patients with clinical feature are receiving treatment/intervention?",
                     "value": "Clinical_Features_Treatment_Intervention"},
                    {"label": "What proportion of patient outcome recieved treatment/intervention?",
                     "value": "Patient_Outcome_Treatment_Intervention"},
                    {"label": "What duration of treatment/intervention is being used in patient outcome?",
                     "value": "Duration_Treatment_Intervention_Patient_Outcome"},

                ]
            else:
                options = []

            question_options = html.Div(
                [
                    dbc.RadioItems(
                        id="row2_radios",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                        options=options,
                    ),
                    html.Div(id="rq_questions_div"),
                ],
                className="radio-group",
            )

            return question_options

        @app.callback(
            [
                Output('row3_tabs', 'children'),
                Output('selected_question', 'children')
            ],
            [
                Input('row2_radios', 'value')
            ],
            [
                State('selected_data-store', 'data')
            ],
        )
        def update_row3_content(selected_value, json_data):
            config_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'assets', 'config_files')
            research_question_elements = pd.read_csv(join(config_dir, 'researchQuestions.csv'))

            group_elements = []
            for tq_opGroup in research_question_elements['Option Group'].unique():
                all_elements = []
                for rq_element in research_question_elements['Relavent variable names on ARC'].loc[
                    research_question_elements['Option Group'] == tq_opGroup]:
                    if type(rq_element) == str:
                        for rq_aux in rq_element.split(';'):
                            all_elements.append(rq_aux.strip())
                group_elements.append([tq_opGroup, all_elements])

            group_elements = pd.DataFrame(data=group_elements, columns=['Group Option', 'Variables'])

            if json_data is None:
                selected_variables_fromData = None
            else:
                selected_variables_fromData = pd.read_json(json_data, orient='split')
                selected_variables_fromData = selected_variables_fromData[['Variable', 'Form', 'Section', 'Question']]

            tabs_content = []
            selected_question = ''

            if selected_value == "CD_Features":
                OptionGroup = ["Case Defining Features"]
                caseDefiningVariables = group_elements['Variables'].loc[
                    group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_features = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(caseDefiningVariables.iloc[0]))],
                    'case_feat',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(dbc.Tab(label="Features", children=[html.P(" "), paralel_elements_features]))
                selected_question = "What are the [case defining features]?"

            elif selected_value == "Spectrum_Clinical_Features":
                OptionGroup = ["Clinical Features"]
                clinicalVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_features = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(clinicalVariables.iloc[0]))],
                    'clinic_feat',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(
                    dbc.Tab(label="Clinical Features", children=[html.P(" "), paralel_elements_features]))
                selected_question = "What is the spectrum of [clinical features] in this disease?"

            elif selected_value == "Clinical_Features_Patient_Outcome":
                OptionGroup = ["Clinical Features"]
                clinicalVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_features = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(clinicalVariables.iloc[0]))],
                    'clinic_feat',
                    CURRENT_DATADICC, selected_variables_fromData)
                OptionGroup = ["Patient Outcome"]
                outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_outcomes = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(
                    dbc.Tab(label="Clinical Features", children=[html.P(" "), paralel_elements_features]))
                tabs_content.append(
                    dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))
                selected_question = "What are the [clinical features] occuring in those with [patient outcome]?"

            elif selected_value == "Risk_Factors_Patient_Outcome":
                OptionGroup = ["Risk Factors: Demographics",
                               "Risk Factors: Socioeconomic", "Risk Factors: Comorbidities"]
                riskVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                allRiskVarr = []
                for rv in riskVariables:
                    allRiskVarr += list(rv)
                paralel_elements_risk = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(allRiskVarr)],
                    'risk', CURRENT_DATADICC, selected_variables_fromData)
                OptionGroup = ["Patient Outcome"]
                outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_outcomes = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(dbc.Tab(label="Risk Factors", children=[html.P(" "), paralel_elements_risk]))
                tabs_content.append(
                    dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))
                selected_question = "What are the [risk factors] for [patient outcome]?"

            elif selected_value == "Treatment_Intervention_Patient_Outcome":

                OptionGroup = ["Treatment/Intevention"]
                TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_treatments = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(TreatmentsVariables.iloc[0]))],
                    'treatment',
                    CURRENT_DATADICC, selected_variables_fromData)
                OptionGroup = ["Patient Outcome"]
                outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_outcomes = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(
                    dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))
                tabs_content.append(
                    dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))

                selected_question = "What [treatment/intervention] are received by those with  [patient outcome]?"
            elif selected_value == "Clinical_Features_Treatment_Intervention":

                selected_question = "What proportion of patients with [clinical feature] are receiving [treatment/intervention]?"

                OptionGroup = ["Clinical Features"]
                clinicalVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_features = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(clinicalVariables.iloc[0]))],
                    'clinic_feat',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(
                    dbc.Tab(label="Clinical Features", children=[html.P(" "), paralel_elements_features]))
                OptionGroup = ["Treatment/Intevention"]
                TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_treatments = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(TreatmentsVariables.iloc[0]))],
                    'treatment',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(
                    dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))

            elif selected_value == "Patient_Outcome_Treatment_Intervention":
                OptionGroup = ["Treatment/Intevention"]
                TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_treatments = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(TreatmentsVariables.iloc[0]))],
                    'treatment',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(
                    dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))

                OptionGroup = ["Patient Outcome"]
                outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_outcomes = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(
                    dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))

                selected_question = "What proportion of [patient outcome] recieved [treatment/intervention]?"
            elif selected_value == "Duration_Treatment_Intervention_Patient_Outcome":
                OptionGroup = ["Treatment/Intevention"]
                TreatmentsVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_treatments = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(TreatmentsVariables.iloc[0]))],
                    'treatment',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(
                    dbc.Tab(label="Treatments/Interventions", children=[html.P(" "), paralel_elements_treatments]))

                OptionGroup = ["Patient Outcome"]
                outcomeVariables = group_elements['Variables'].loc[group_elements['Group Option'].isin(OptionGroup)]
                paralel_elements_outcomes = parallel_elements(
                    CURRENT_DATADICC.loc[CURRENT_DATADICC['Variable'].isin(list(outcomeVariables.iloc[0]))], 'outcome',
                    CURRENT_DATADICC, selected_variables_fromData)
                tabs_content.append(
                    dbc.Tab(label="Patient Outcomes", children=[html.P(" "), paralel_elements_outcomes]))
                selected_question = "What duration of [treatment/intervention] is being used in [patient outcome]?"

            parts = re.split(r'(\[.*?\])', selected_question)  # Split by text inside brackets, keeping the brackets

            styled_parts = []
            for part in parts:
                if part.startswith('[') and part.endswith(']'):
                    # Text inside brackets, apply red color
                    styled_parts.append(html.Span(part, style={'color': '#BA0225'}))
                else:
                    # Regular text, no additional styling needed
                    styled_parts.append(html.Span(part))
            # Add more conditions as necessary for other options

            return tabs_content, styled_parts

        def parallel_elements(features, id_feat, current_datadicc, selected_variables):
            text = feature_text(current_datadicc, selected_variables, features)
            accord = feature_accordion(features, id_feat, selected=selected_variables)

            pararel_features = html.Div([
                # First column with the title and the Available Columns table
                html.Div([
                    html.H5('Available Features', style={'textAlign': 'center'}),
                    accord

                ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                # Second column with the buttons
                html.Div(style={'width': '1%', 'display': 'inline-block', 'textAlign': 'center'}),

                # Third column with the title and the Display Columns table
                html.Div([
                    html.H5('Selected Features', style={'textAlign': 'center'}),
                    dcc.Markdown(id=id_feat + '_text-content', children=text,
                                 style={'height': '300px', 'overflowY': 'scroll', 'border': '1px solid #ddd',
                                        'padding': '10px',
                                        'color': 'black'}),

                ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            ], style={'width': '100%', 'display': 'flex'})
            return pararel_features

        def feature_text(current_datadicc, selected_variables, features):
            selected_variables = selected_variables.copy()
            selected_variables = selected_variables.loc[selected_variables['Variable'].isin(features['Variable'])]
            if (selected_variables is None):
                return ''
            else:
                text = ''
                selected_features = current_datadicc.loc[
                    current_datadicc['Variable'].isin(selected_variables['Variable'])]
                for sec in selected_features['Section'].unique():
                    # Add section title in bold and a new line
                    text += f"\n\n**{sec}**\n"
                    for label in selected_features['Question'].loc[selected_features['Section'] == sec]:
                        # Add each label as a bullet point with a new line
                        text += f"  - {label}\n"
                return text

        def feature_accordion(features, id_feat, selected):
            feat_accordion_items = []
            cont = 0

            for sec in features['Section'].unique():
                if selected is None:
                    selection = []
                else:
                    selection = selected['Variable'].loc[selected['Section'] == sec]
                    # For each group, create a checklist
                checklist = dbc.Checklist(
                    options=[{"label": row['Question'], "value": row['Variable']} for _, row in
                             features.loc[features['Section'] == sec].iterrows()],
                    value=selection,
                    id=id_feat + '_' + f'checklist-{str(cont)}',
                    switch=True,
                )
                cont += 1
                # Create an accordion item with the checklist
                feat_accordion_items.append(
                    dbc.AccordionItem(
                        title=sec.split(":")[0],
                        children=html.Div(checklist, style={'height': '100px', 'overflowY': 'auto'})
                    )
                )
            return dbc.Accordion(feat_accordion_items)

        return app
