# PyWarnFixer: Using ML to fix Pylint warnings

## Introduction

Welcome to the project repository for our research study titled "PyWarnFixer: Using ML to fix Pylint warnings" This study, conducted by researchers from TU Delft, aims to investigate the perceptions and practices of code quality among developers in Python open-source projects. In addition, we are developing a tool that utilizes AI to automatically fix pylint warnings.

## Research Objectives

The primary objectives of this research are to gain insights into the most common pylint warnings in open-source Python projects, to understand how developers respond to proposed fixes for these warnings, and to develop an AI-powered tool that automatically addresses these pylint warnings.

## Process Overview

The research begins with a project collection script that searches for open-source Python projects on GitHub that accept pull requests. Once suitable projects are identified, the script analyzes these repositories for pylint warnings. To address the identified pylint warnings, the script uses a third-party AI service. It sends code snippets containing warnings to the AI, which returns corrected code snippets. These fixes are then integrated into the codebase.

Next, pull requests are created for these proposed fixes in the respective projects. Each pull request includes detailed information about the changes made by the tool and an explanation that the pull request is part of a research project conducted by TU Delft. Additionally, the pull request provides a link to the research project's information page (this README) and includes a request for consent with clear instructions on how to give consent via GitHub authentication.

Upon encountering our pull request, reviewers are prompted to give explicit consent to participate in the research. This involves authenticating through GitHub to confirm their identity, by creating an issue stating that they give consent. This is done by using an [issue template](https://github.com/RatishT/PyWarnFixer/issues/new/choose). The process is designed to be user-friendly, allowing reviewers to provide consent with just a few clicks. We maintain an issue board within our GitHub repository that lists reviewers who have given consent, ensuring transparency and traceability. Each issue corresponds to a specific reviewer, identifiable by their GitHub ID.

After providing consent, reviewers proceed to review the pull request as they normally would. We document their review comments, noting whether the proposed changes were accepted or rejected, and record the GitHub ID of the reviewer who handled the pull request. This data is securely stored and anonymized to protect participants' identities while allowing us to analyze the effectiveness and reception of the proposed code fixes.

## Ethical Considerations

By integrating the consent procedure into the pull request process, we ensure that explicit consent is obtained efficiently and ethically. This approach aligns with best practices in research ethics and sets a higher standard for transparency and participant autonomy in studies involving publicly available data. Our commitment to ethical research practices underscores the importance we place on the rights and privacy of all contributors to open-source projects.

## Contact Information

For more information about the research project, or if you have any questions or concerns, please contact the Responsible Researcher at R.K.Thakoersingh@student.tudelft.nl.

Thank you for your interest and possible participation in this research endeavor.