# Git Branch Naming Convention and Best Practices

## 1 Git Branch Types

Based on the **lifecycle** of different Git branches and the **types of changes** they introduce, Git branches can generally be divided into two categories:

- Regular branches
- Temporary branches

This classification helps teams manage their Git workflow more effectively. Proper naming ensures that long-lived branches remain stable, while temporary branches are used for specific short-term tasks without cluttering the repository history.

The following sections explain these two types in detail.

## 2 Regular Git Branches

Regular branches in Git are long-lived branches that provide a stable and structured way to organize ongoing work. These branches are permanently available in the [repository](https://phoenixnap.com/glossary/what-is-a-repository), and their naming is usually straightforward.

Some regular Git branches include:

- **Master (master/main) branch.** The default production branch in a [Git repository](https://phoenixnap.com/kb/what-is-a-git-repository) that must remain permanently stable. Developers can merge changes into the master branch only after code review and testing. All collaborators on a project must keep the master branch stable and up to date.
- **Development (dev) branch.** The main development branch that serves as a central hub for developers to integrate new features, bug fixes, and other changes. Its primary purpose is to provide a place for changes so that developers do not implement them directly in the master branch. Developers test, review, and [merge the changes from the dev into the master branch](https://phoenixnap.com/kb/git-merge-branch-into-master).
- **QA (QA/test) branch**. The branch that contains all the code ready for [QA](https://phoenixnap.com/glossary/what-is-quality-assurance) and automation testing. QA testing is necessary before implementing any change in the production environment to maintain a stable codebase.

## 3 Temporary Git Branches

Temporary branches are short-lived and disposable. These branches serve specific, short-term purposes and are often deleted afterward.

Some temporary branches in Git include:

- **Bugfix branch.** A bugfix branch contains code with bugs that require prompt fixes. It can also hold rejected code from feature branches that needs fixing before implementation.
- **Hotfix branch.** A hotfix branch is used to implement a temporary solution for buggy code without following the usual procedure. It is used in emergencies when a fast fix is needed. Developers merge the hotfix branch directly into the production branch and later into the development branch.
- **Feature branch.** A feature branch is used to add, reconfigure, or remove a feature. It is based on the development branch. After the changes are made, developers merge the feature branch back into the development branch.
- **Experimental branch.** This branch is used to develop new features or ideas that are not part of a release or a sprint. It is a branch for trying out new things.
- **WIP (work in progress) branch.** Developers use WIP branches to develop or try out new features. These branches are not necessarily part of the regular development workflow. WIP branches are project-specific and often informal, with no specific or standardized rules.
- **Merging branch.** A merging branch is a temporary branch used for resolving merge conflicts. Conflicts can arise when merging the latest development branch and a feature or hotfix branch into another branch. A merging branch is also useful when combining two feature branches developed by multiple contributors. This process involves merging, verifying, and finalizing the changes.

Two example open source repositories are:

- [GitHub - microsoft/vscode: Visual Studio Code](https://github.com/microsoft/vscode)
- [GitHub - kubernetes/kubernetes: Production-Grade Container Scheduling and Management](https://github.com/kubernetes/kubernetes)

## 4 Git Branch Naming Best Practices

### 4.1 Use Hyphens and Slashes as Separators

One of the most common naming conventions is to use slashes (`/`) or hyphens (`-`) as separators in branch names. These symbols make branch names easier to read because you do not need to focus on identifying where one word ends and the next begins.

For example, compare the following branch names:

```text
featurenewuserregistrationworkflowwithemailverification
```

and

```text
feature/new-user-registration-workflow-with-email-verification
```

The second branch name is descriptive and provides information about the purpose of the branch, in this case adding a new user registration workflow with email verification. Using separators such as slashes and hyphens makes the purpose much easier to recognize.

Also, branch names should be kept as short as possible. For example, the above name could be shortened to:

```text
feature/email-verification-workflow
```

The main advantages of using separators are:

- Improved readability and reduced confusion
- Easier management, especially when working with many branches
- Better naming consistency by using lowercase letters and separating words with hyphens or slashes

### 4.2 Use Numbers

If the feature currently being developed is associated with a requirement, task, or issue, you can include the requirement ID in the branch name. The ID helps track the development progress of that requirement on the branch.

For example:

```text
wip/8712-add-login-module
```

From this name, it is immediately clear that the branch is a work-in-progress branch and that its requirement ID is 8712.

### 4.3 Use Category Words

A common practice is to start branch names with a category word that identifies the branch's purpose. Category words usually describe the branch type, such as:

- bugfix
- hotfix
- wip
- feature

Using categories helps developers working on the same project understand the purpose of a branch. The category word is usually separated from the rest of the branch name with a slash (`/`).

For example:

```text
bugfix/fix-login-error
```

The purpose of this branch is to fix a login error, and it was created specifically for that purpose.

### 4.4 Use the Author's Name

Another naming convention is to include the author's name in the Git branch name to clarify which developer has worked on the branch. This makes it easy to track who is working on a feature. The author's name is usually the first element in the branch name.

For example:

```text
john/feature/add-user-profile
```

In this example, the branch name starts with the author's name, followed by a slash separating it from the branch type. The rest of the name describes the branch purpose, which is to add a user profile feature.

### 4.5 Combine Multiple Naming Conventions When Appropriate

Several Git branch naming conventions can be used together. However, avoid applying every rule to every branch name. Instead, combine them naturally and clearly to maintain readability.

For example:

```text
feature/user-registration-system/bugfix/1234-issue
```

This name uses multiple naming conventions and indicates a branch related to a user registration system with requirement or issue ID 1234.

## 5 Resources

- [Git Branch Name Convention: 6 Best Practices to Follow](https://phoenixnap.com/kb/git-branch-name-convention)
- [Git Branching Strategies: What Are Different Branching Strategies?](https://phoenixnap.com/kb/git-branching-strategy)
- [GitHub - aseaday/git-style-guide: A Git Style Guide](https://github.com/aseaday/git-style-guide)
- [A successful Git branching model » nvie.com](https://nvie.com/posts/a-successful-git-branching-model/)
