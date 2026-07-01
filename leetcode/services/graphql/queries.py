VERIFY_COOKIES_QUERY = """
    query {
      userStatus {
        username
        isSignedIn
      }
    }
    """

GET_PROFILE_QUERY = """
    query {
      userStatus {
        username
        realName
        avatar
        isSignedIn
      }
    }
    """

GET_USER_PUBLIC_PROFILE_QUERY = """
    
    query userPublicProfile($username: String!) {
      matchedUser(username: $username) {
        isBlocked
        isBlocker
        contestBadge {
          name
          expired
          hoverText
          icon
        }
        username
        githubUrl
        twitterUrl
        linkedinUrl
        profile {
          ranking
          userAvatar
          realName
          aboutMe
          school
          websites
          countryName
          company
          jobTitle
          skillTags
          postViewCount
          postViewCountDiff
          reputation
          reputationDiff
          solutionCountDiff
          categoryDiscussCountDiff
          certificationLevel
          isFollowingMe
          isFollowedByMe
          hideFollowers
          hideFollowing
        }
      }
      ugcArticleUserSolutionArticles(username: $username, skip: 0, first: 0) {
        totalNum
      }
      ugcArticleUserDiscussionArticles(username: $username, skip: 0, first: 0) {
        totalNum
      }
    }
  """

LATEST_SUBMISSION_QUERY = """
    query recentSubmissionList($username: String!) {
      recentSubmissionList(username: $username) {
        id
        title
        titleSlug
        statusDisplay
        lang
        timestamp
      }
    }
    """

GET_SUBMISSION_QUERY = """
    query submissionDetails($submissionId: Int!) {
        submissionDetails(submissionId: $submissionId) {
            runtime
            runtimeDisplay
            runtimePercentile
            runtimeDistribution
            memory
            memoryDisplay
            memoryPercentile
            memoryDistribution
            code
            timestamp
            statusCode
            aiJudgeMessage
            isCompiledLang
            aiRecheckSubmitted
            user {
            username
            profile {
                realName
                userAvatar
            }
            }
            lang {
            name
            verboseName
            }
            question {
            questionId
            titleSlug
            hasFrontendPreview
            }
            notes
            flagType
            topicTags {
            tagId
            slug
            name
            }
            runtimeError
            compileError
            lastTestcase
            codeOutput
            expectedOutput
            totalCorrect
            totalTestcases
            fullCodeOutput
            testDescriptions
            testBodies
            testInfo
            stdOutput
        }
    }
    """

GET_SOLVED_STATS = """
    query userProblemsSolved($username: String!) {
      matchedUser(username: $username) {
        submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
            submissions
          }
        }
        profile {
          ranking
          reputation
          starRating
        }
        contributions {
          points
        }
      }
    }
    """

GET_SUBMISSIONS_QUERY = """
    query submissionList(
      $offset: Int!
      $limit: Int!
      $lastKey: String
      $questionSlug: String
    ) {
      submissionList(
        offset: $offset
        limit: $limit
        lastKey: $lastKey
        questionSlug: $questionSlug
      ) {
        lastKey
        hasNext
        submissions {
          id
          title
          titleSlug
          statusDisplay
          lang
          timestamp
          runtime
          memory
        }
      }
    }
"""

GET_TOPIC_STATS_QUERY = """
    query skillStats($username: String!) {
      matchedUser(username: $username) {
        tagProblemCounts {
          advanced {
            tagName
            tagSlug
            problemsSolved
          }
          intermediate {
            tagName
            tagSlug
            problemsSolved
          }
          fundamental {
            tagName
            tagSlug
            problemsSolved
          }
        }
      }
    }
"""
    
GET_LANG_STATS_QUERY = """
  query languageStats($username: String!) {
    matchedUser(username: $username) {
      languageProblemCount {
        languageName
        problemsSolved
      }
    }
  }
"""

GET_SUBMISSION_LIST_QUERY = """
    query submissionList($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!, $lang: Int, $status: Int) {
      questionSubmissionList(
        offset: $offset
        limit: $limit
        lastKey: $lastKey
        questionSlug: $questionSlug
        lang: $lang
        status: $status
      ) {
        lastKey
        hasNext
        submissions {
          id
          title
          titleSlug
          status
          statusDisplay
          lang
          langName
          runtime
          timestamp
          url
          isPending
          memory
          hasNotes
          notes
          flagType
          frontendId
          topicTags {
            id
          }
        }
      }
    }
  """
    
GET_PROBLEM_DETAIL_QUERY = """
  query questionDetail($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
      title
      titleSlug
      questionId
      questionTitle
      content
      translatedContent
      categoryTitle
      difficulty
      stats
      topicTags {
        name
        slug
        translatedName
      }
      mysqlSchemas
      dataSchemas
      likes
      dislikes
      metaData
      hints
      codeSnippets {
        code
        lang
        langSlug
      }
      exampleTestcaseList
      featuredContests {
        titleSlug
        title
      }
    }
  }
"""
    
GET_SIMILAR_PROBLEMS_QUERY = """
  query questionDetail($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
      similarQuestionList {
        difficulty
        titleSlug
        title
        translatedTitle
        isPaidOnly
      }
      nextChallenges {
        difficulty
        title
        titleSlug
        questionFrontendId
      }
    }
  }
"""

GET_DAILY_PROBLEM_QUERY = """
  query questionOfTodayV2 {
    activeDailyCodingChallengeQuestion {
      date
      userStatus
      link
      question {
        id: questionId
        titleSlug
        title
        translatedTitle
        questionFrontendId
        paidOnly: isPaidOnly
        difficulty
        topicTags {
          name
          slug
          nameTranslated: translatedName
        }
        status
        isInMyFavorites: isFavor
        acRate
        frequency: freqBar
      }
    }
  }
"""

GET_CONTEST_RATING_QUERY = """  
  query userContestRanking($username: String!) {
    userContestRanking(username: $username) {
      attendedContestsCount
      rating
      globalRanking
      totalParticipants
      topPercentage
      badge {
        name
      }
    }
  }
"""

GET_CONTEST_HISTORY_QUERY = """
  query userContestRankingInfo($username: String!) {
    userContestRankingHistory(username: $username) {
      attended
      trendDirection
      problemsSolved
      totalProblems
      finishTimeInSeconds
      rating
      ranking
      contest {
        title
        startTime
      }
    }
  }
"""

GET_CONTEST_QUESTION_QUERY = """
  query contestQuestionList($contestSlug: String!) {
    contestQuestionList(contestSlug: $contestSlug) {
      isAc
      credit
      title
      titleSlug
      titleCn
      questionId
      isContest
    }
  }
"""

GET_UPCOMING_CONTESTS_QUERY = """
  query upcomingContests {
    topTwoContests {
      title
      titleSlug
      startTime
      duration
      cardImg
    }
  }
"""


