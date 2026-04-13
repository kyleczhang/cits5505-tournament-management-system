# Project Description, Rubric and FAQs

## Introduction

This assessment will determine your attainment of the following unit learning outcomes:

- explain the key components that work together to enable the delivery of data and services on today's internet
- understand the technologies behind the terms and how they fit together, and back this up with examples of hands-on programming experience
- develop web applications using client side and server side technologies.
- explain and apply agile project methodologies.

## Project Structure

For this project you are required to build a web-application of your choice.

The key requirements are:

- It must use a client-server architecture.
- It must have the ability for users to login and logout.
- User data must be persisted between user sessions.
- Users must have the ability to view data from other users in some manner.

You will be marked not just on your code but also the design of the application. It should be:

- _Engaging_, so that it looks good and focuses the user on important elements of the application.
- _Effective_, so it produces value for the user, by providing information, entertainment or community.
- _Intuitive_, so that it is easy for a user to use.

**Note 1**: It is not expected that you know how to build such an application now, nor that you get started on the project immediately! We will teach you how to do these things.

**Note 2:** If you do already have some experience in web-development, **do not** rush ahead of other members of group. This is a project that you are supposed to do as a group, so please wait until we have covered the relevant contents in the course. **A large portion of the marks will be given for your personal ability to work in a team so if you do end up trying to complete the project solo without trying to involve other people, you will end up with a much lower mark than you are expecting.**

## Technical Specification

The list of core allowable technologies and libraries are the following:

- HTML
- CSS
- JavaScript
- A CSS Framework that is either Bootstrap/Tailwind/SemanticUI/Foundation (no others allowed).
- JQuery
- Flask + plugins described in lectures
- AJAX/Websockets
- SQLite interfaced to via the SQLAlchemy package

You **may not** use any other core technologies, this includes frameworks (e.g. React/Angular), database systems (e.g. MySQL), or advanced CSS frameworks (e.g. directly using SASS yourself).

However, you **may** freely use any JavaScript or Python libraries that implement non-core functionality that is particular to your application, e.g. libraries that provide bindings for ChatGPT or displaying graphs is fine! Font and icon libraries are also fine.

The creation of the web application should be done in a public GitHub repository that includes a README containing:

1. a description of the purpose of the application, explaining its design and use.
2. a table with with each row containing the i) UWA ID ii) name and iii) Github user name of the group members.
3. instructions for how to launch the application.
4. instructions for how to run the tests for the application.

## Possible Project Ideas

For example, the application could be:

- An exercise tracking application, where users track their exercise habits, can view stats about their habits, and share information about their achievements with their friends on the system.
- A persistent online game, which saves the user's progress and allows players to interact with each other in some manner.
- A course-selector tool, allowing users to upload details (e.g. times, duration, credit hours) of courses they are interested in taking, and then run scheduling algorithms to generate a plausible selection of units, and allowing users to share suggested schedules with their classmates.
- A tournament management system, where users can input results of sports/board games tournaments, see player stats, and then share results with other users.
- An infectious disease monitoring system where users can upload datasets of infections, and the application will plot them on a map and you can share areas with high outbreaks to other users.
- A news sentiment analysis tool, allowing users to upload or input news content, and then analyse the text using NLP algorithms (e.g., sentiment scoring) to determine overall sentiment, and share the analysed data with their colleagues.
- A social media site, where users can post and see other users' content.

## Assessment Structure

The group project will be split into 3 checkpoints. **_Attendance of each checkpoint meeting is compulsory_**.  At each checkpoint, the whole of your group will meet in person with your lab facilitator (see Group Allocations below). Please see the Group Project folder on the main page for what is expected at each checkpoint.

- **Checkpoint 1** - **Weeks 2-4:** Introductions and Git/GitHub ability demonstration.
- **Checkpoint 2 - Weeks 5-7:** Planning and Frontend UI
- **Checkpoint 3 - Weeks 8-10**: Backend Implementation

The project is then due at the very end of Week 11.

- **Project Presentations - Week 12**: Final presentation of your project.

## Marking Rubric

The marking will be split up into three components:

- **Overall Application** - The quality of the application produced. Marks are usually shared by everyone in the group equally.

|             |                                                                                                                                                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Content     | All the features requested in the project brief are implemented appropriately.                                                                                                                                      |
| Design      | Good website navigation flow that is intuitive to the user with a strong visual design. The website's purpose is clear and brings value to the user. These marks will be used to distinguish the very top projects. |
| HTML        | Valid HTML code, using a wide range of elements, clearly organised with appropriate use of Jinja templates.                                                                                                         |
| CSS         | Valid, maintainable code, using a wide range of custom selectors and classes, web page is reactive to screen size.                                                                                                  |
| JavaScript  | Valid, well formatted code, including validation and DOM manipulation/AJAX that uses JavaScript best practices.                                                                                                     |
| Flask Code  | Formatted, commented and well organised code that responds to requests by the client by performing non-trivial data manipulation and page generation operations.                                                    |
| Data Models | Well considered database schema, good authentication, and maintainable models. Some evidence of DB migrations.                                                                                                      |
| Testing     | Comprehensive test suite, containing 5+ unit tests and 5+ selenium tests. The latter should run with a live version of the server.                                                                                  |
| Security    | Passwords correctly stored as salted hashes in database. Use of CRSF tokens to prevent CRSF attacks on the website's forms. Correct storage of environment variables in configuration files.                        |

- **Agile Development** **Process** - Your personal use of Git and GitHub to collaborate and plan during the project and attendance at the check-point meetings. Marks are allocated individually.

|                     |                                                                                                                                                                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Checkpoint Meetings | Are you demonstrating engagement with the project during Checkpoint meetings?                                                                                                                                                         |
| Commits             | Regular commits with high-quality messages providing meaningful but not overly detailed description of and reason for the changes.                                                                                                    |
| Issues              | Use of the GitHub Issues, with issues regularly used both to describe both bugs and missing functionality. The former have detailed instructions about how to reproduce.                                                              |
| Pull requests       | Use of the GitHub Pull Requests, with meaningfully named pull requests regularly used to both add new features and fix bugs.                                                                                                          |
| Teamwork            | Evidence of collaboration between team members on GitHub, including in-depth discussion on other people's issues, and helpful code reviews on other people's pull requests with the feedback being taken into account before merging. |

- **Teamwork Marks** - A small number of bonus marks, that are allocated by the group at their discretion to reward members of the team who went above and beyond during the project.

**Note**: Although the "Overall Application" marks are usually shared equally by everyone, you must make non-trivial contributions to the project to earn your share. Over 95% of students achieve this, but in rare cases where the facilitator and unit coordinators have judged that someone has not made meaningful contributions to the project, that person may only receive some fraction of the group mark. It is usually very obvious to the student themself if they are not contributing to the project, but we will do our best to warn you during the checkpoint meetings if you are in danger of not meeting the contribution threshold.
