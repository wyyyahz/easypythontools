import requests
import json
import pandas as pd
import time
import uuid
from datetime import datetime, timedelta

def run(max_pages=None, city_id=5818, city_name="武汉",
        checkin="2026-06-01", los=1, adults=2, page_size=25):
    """
    抓取 Agoda 酒店数据 - 修复 pageToken 问题，支持完整抓取所有页面
    """

    url = "https://www.agoda.cn/graphql/search"

    # ✅ 更新点 1: Headers
    # 从 copyAllAsCurl.txt 中提取的 GraphQL 请求 Headers
    headers = {
        'authority': 'www.agoda.cn',
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'ag-cid': '-1',
        'ag-debug-override-origin': 'CN',
        'ag-language-locale': 'zh-cn',
        'ag-page-type-id': '103',
        'ag-request-attempt': '1',
        'ag-whitelabel-key': 'F1A5905F-9620-45E5-9D91-D251C07E0B42',
        'content-type': 'application/json',
        'origin': 'https://www.agoda.cn',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'x-gate-meta': 'MTc3ODA2MDgxODE4NHxlOGE5YzY3My04MDFiLTQ5YWMtYTVlZi0xYjU0ZDZiZWJkOGN8L2dyYXBocWwvc2VhcmNo' # 此值可能有时效性，若失效需重新抓包
    }

    # ✅ 更新点 2: Cookie
    # 从 copyAllAsCurl.txt 中提取的 Cookie (注意：Cookie 通常有过期时间，长期运行可能需要定期更新)
    headers['cookie'] = 'agoda.user.03=UserId=e8a9c673-801b-49ac-a5ef-1b54d6bebd8c; agoda.prius=PriusID=0&PointsMaxTraffic=Agoda; ASP.NET_SessionId=2k0ml3ehasishfubyhzqwu1p; agoda.landings=-1|||2k0ml3ehasishfubyhzqwu1p|2026-05-06T13:33:04|False|19-----1|||2k0ml3ehasishfubyhzqwu1p|2026-05-06T13:33:04|False|20-----1|||2k0ml3ehasishfubyhzqwu1p|2026-05-06T13:33:04|False|99; agoda.attr.fe=-1|||2k0ml3ehasishfubyhzqwu1p|2026-05-06T13:33:04|False|2026-06-05T13:33:04|KJU5+IxJ/jMUUlRS; agoda.attr.03=ATItems=-1$05-06-2026 13:33$; deviceId=1138415b-6b0d-48b9-b01e-08ca2c7cb03f; agoda.price.01=PriceView=2; _ab50group=GroupB; _40-40-20Split=Group20; _ga=GA1.2.1891941631.1778049409; _gid=GA1.2.1341203801.1778049409; _uetsid=f74fcce0491511f1983a497a022e019c|1kgix47|2|g5t|0|2317; cto_bundle=HnPU719QRGNBOTNFQXBuJTJGJTJCRjhMRVVpMWowJTJCYzJROTZUUldSSW1hJTJGb0dHWmVqWUNTSVM0YUVmMkJxM0tDJTJGWnhhYzBLVEhjS3NaTXhWVUMxUG5JeHNreWVIeVpwUk10T1dpJTJGMSUyQjVOZGkxM1BVVHBXT2d1NGc1VkJLdEZ5dkZXa3pSbDZQZmtTaUdMMFI3YzVaJTJGeUxaREdFdjdRJTNEJTNE; _uetvid=f7500390491511f198e19731613a6860|ljd6lq|1778050087989|2|1|bat.bing.com/p/conversions/c/z; _ga_C07L4VP9DZ=GS2.2.s1778053830$o2$g0$t1778053830$j60$l0$h0; agoda.version.03=CookieId=a8e92362-e0b2-4153-a404-87f4013badd1&DLang=zh-cn&CurLabel=CNY&CuLang=8; agoda.search.01=SHist=1$9395$9256$1$1$2$0$0$$$|1$5818$9256$1$1$2$0$0$$$; agoda.consent=CN||2026-05-06 08:43:31Z; t_pp=XR/lV/DdDuQjDWet:Dy01FE7c6dqYZ4AeKx3/jg==:RWXzK/LOLVPfJfDOZlceoRWR4h3WEx/QIkgQJlVH4ZPWDHDwf1jjSVC2r8EIofzXgebKVt2Fo36LXeuiNFdOpLRNbJe/UGAj3UVnrtOtgH9e9DDlNING1XEUHEdiwzcwVhUiKA98UpSPzviCzgXFLWUsNZRReSBUjrGJ0C84AvB/TLYxPUf1VTnD5LB+M4f98XEPK6ArP+oUOBMT5h10EeBB/SrtGBtAcySKeZCfUjlNACFXIpS/nw==; utag_main=v_id:019dfbfdce5200170beb836a098a0506a001506200bd0$_sn:3$_se:1$_ss:1$_st:1778062602832$ses_id:1778060802832%3Bexp-session$_pn:1%3Bexp-session; __gads=ID=97be0ab7088fc6ec:T=1778049198:RT=1778060788:S=ALNI_MZcXos6Dq-OgrALXuaKB0zvJPZbxQ; __gpi=UID=000013f751ed1070:T=1778049198:RT=1778060788:S=ALNI_MaGyNCkaq7_hUWZht3bzUm9zLHdeg; agoda.analytics=Id=-2770737844507481522&Signature=6241372280871885581&Expiry=1778064387905; t_rc=dD03MSZ1aWQ9ZThhOWM2NzMtODAxYi00OWFjLWE1ZWYtMWI1NGQ2YmViZDhj.6RSooWokT/JIfQjY17sk3xpc4P4bBmSCw7d0OQZqrcA='

    checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
    checkout_date = checkin_date + timedelta(days=los)
    checkin_str = checkin_date.strftime("%Y-%m-%dT00:00:00.000Z")

    search_id = str(uuid.uuid4())

    # 完整的 GraphQL 查询（保持原样以确保得到正确的 pageToken）
    graphql_query = """query citySearch($CitySearchRequest: CitySearchRequest!, $ContentSummaryRequest: ContentSummaryRequest!, $PricingSummaryRequest: PricingRequestParameters, $PriceStreamMetaLabRequest: PriceStreamMetaLabRequest) {
  citySearch(CitySearchRequest: $CitySearchRequest) {
    searchResult {
      sortMatrix {
        result {
          fieldId
          sorting {
            sortField
            sortOrder
            sortParams {
              id
            }
          }
          display {
            name
          }
          childMatrix {
            fieldId
            sorting {
              sortField
              sortOrder
              sortParams {
                id
              }
            }
            display {
              name
            }
            childMatrix {
              fieldId
              sorting {
                sortField
                sortOrder
                sortParams {
                  id
                }
              }
              display {
                name
              }
            }
          }
        }
      }
      searchInfo {
        hasSecretDeal
        isComplete
        hasEscapesPackage
        totalActiveHotels
        totalFilteredHotels
        objectInfo {
          objectName
          mapLatitude
          mapLongitude
          mapZoomLevel
          cityName
          countryId
          countryName
          cityId
        }
        searchStatus {
          searchStatus
          searchCriteria {
            checkIn
          }
        }
        pollingInfoResponse {
          pollId
          pollAttempt
          shouldPoll
          suggestedPollIntervalMs
        }
      }
      histogram {
        bins {
          numOfElements
          upperBound {
            perNightPerRoom
            perPax
          }
        }
        maxMinPrice {
          perRoomPerNight {
            max
            min
          }
        }
      }
      nhaProbability
    }
    properties(ContentSummaryRequest: $ContentSummaryRequest, PricingSummaryRequest: $PricingSummaryRequest, PriceStreamMetaLabRequest: $PriceStreamMetaLabRequest) {
      propertyId
      sponsoredDetail {
        sponsoredType
        trackingData
        isShowSponsoredFlag
      }
      propertyResultType
      content {
        rateCategories {
          escapeRateCategories {
            rateCategoryId
            localizedRateCategoryName
          }
        }
        informationSummary {
          localeName
          defaultName
          displayName
          accommodationType
          awardYear
          hasHostExperience
          address {
            country {
              id
              name
            }
            countryCode
            city {
              id
              name
            }
            area {
              id
              name
            }
          }
          propertyType
          rating
          agodaGuaranteeProgram
          remarks {
            renovationInfo {
              renovationType
              year
            }
          }
          spokenLanguages {
            id
          }
          geoInfo {
            latitude
            longitude
          }
          propertyLinks {
            propertyPage
          }
          highlightedFeatures {
            id
            propertyFacilityName
          }
          nhaSummary {
            hostType
          }
          isSustainableTravel
        }
        propertyEngagement {
          peopleLooking
          todayBooking
        }
        nonHotelAccommodation {
          masterRooms {
            noOfBedrooms
            noOfBeds
            highlightedFacilities
          }
        }
        facilities {
          id
          propertyFacilityName
        }
        images {
          hotelImages {
            id
            caption
            urls {
              key
              value
            }
          }
        }
        reviews {
          contentReview {
            isDefault
            cumulative {
              reviewCount
              score
            }
            demographics {
              groups {
                id
                grades {
                  id
                  score
                }
              }
            }
            summaries {
              recommendationScores {
                recommendationScore
              }
              snippets {
                countryId
                countryCode
                countryName
                date
                demographicId
                demographicName
                reviewer
                reviewRating
                snippet
              }
            }
            providerId
          }
          cumulative {
            score
            scoreText
            maxScore
            reviewCount
            reviewCommentsCount
          }
        }
        familyFeatures {
          hasChildrenFreePolicy
          isFamilyRoom
          hasMoreThanOneBedroom
          isInterConnectingRoom
          isInfantCottageAvailable
          hasKidsPool
          hasKidsClub
        }
        personalizedInformation {
          childrenFreePolicy {
            fromAge
            toAge
          }
        }
        localInformation {
          hasAirportTransfer
        }
        highlight {
          hasNearbyPublicTransportation
          favoriteFeatures {
            features {
              category
              id
              title
            }
          }
          cityCenter {
            isInsideCityCenter
          }
        }
        features {
          hotelFacilities {
            id
            name
          }
        }
      }
      soldOut {
        soldOutPrice {
          averagePrice
        }
      }
      pricing {
        isAvailable
        isReady
        isInsiderDeal
        benefits
        roomBundle {
          bundleId
          bundleType
          saveAmount {
            perNight {
              ...Fragi4ag4943ej703494628c
            }
          }
        }
        pointmax {
          channelId
          point
        }
        payment {
          cancellation {
            cancellationType
          }
          payLater {
            isEligible
          }
          payAtHotel {
            isEligible
          }
          noCreditCard {
            isEligible
          }
          taxReceipt {
            isEligible
          }
        }
        cheapestStayPackageRatePlans {
          stayPackageType
          ratePlanId
        }
        pricingMessages {
          location
          ids
        }
        supplierInfo {
          id
          name
          isAgodaBand
        }
        suppliersSummaries {
          id
          isReady
          supplierHotelId
        }
        offers {
          bundleType
          bundleDetail {
            bundleSegmentRoomIdentifiers {
              roomIdentifier
              quantity
            }
          }
          roomOffers {
            room {
              availableRooms
              isPromoEligible
              supplierId
              stayPackageType
              channel {
                id
              }
              promotions {
                typeId
                promotionDiscount {
                  discountType
                  value
                  showDiscountMessage
                  isFlashDeal
                }
              }
              consolidatedAppliedDiscount {
                totalDiscountJacketMessage
                breakdowns {
                  title
                }
              }
              bookingDuration {
                unit
                value
              }
              pricing {
                currency
                price {
                  perBook {
                    exclusive {
                      display
                      cashbackPrice
                      displayAfterCashback
                      rebatePrice
                      originalPrice
                      autoAppliedPromoDiscount
                    }
                    inclusive {
                      display
                      cashbackPrice
                      displayAfterCashback
                      rebatePrice
                      originalPrice
                      autoAppliedPromoDiscount
                    }
                  }
                  perRoomPerNight {
                    exclusive {
                      display
                      crossedOutPrice
                      cashbackPrice
                      displayAfterCashback
                      rebatePrice
                      pseudoCouponPrice
                      originalPrice
                      loyaltyOfferSummary {
                        basePrice {
                          exclusive
                          allInclusive
                        }
                        status
                        offers {
                          identifier
                          burn {
                            points
                            payableAmount
                            benefitOfferBreakdown {
                              benefitDetails {
                                benefitType
                                category
                                multiplier
                                validFrom
                                validUntil
                              }
                              originalPointsDetails {
                                points
                              }
                              benefitPointsDetails {
                                points
                              }
                            }
                          }
                          earn {
                            points
                          }
                          offerType
                          isSelected
                          status
                        }
                      }
                      autoAppliedPromoDiscount
                    }
                    inclusive {
                      display
                      crossedOutPrice
                      cashbackPrice
                      displayAfterCashback
                      rebatePrice
                      pseudoCouponPrice
                      originalPrice
                      loyaltyOfferSummary {
                        basePrice {
                          exclusive
                          allInclusive
                        }
                        status
                        offers {
                          identifier
                          burn {
                            points
                            payableAmount
                            benefitOfferBreakdown {
                              benefitDetails {
                                benefitType
                                category
                                multiplier
                                validFrom
                                validUntil
                              }
                              originalPointsDetails {
                                points
                              }
                              benefitPointsDetails {
                                points
                              }
                            }
                          }
                          earn {
                            points
                          }
                          offerType
                          isSelected
                          status
                        }
                      }
                      autoAppliedPromoDiscount
                    }
                  }
                  perNight {
                    exclusive {
                      originalPrice
                    }
                    inclusive {
                      originalPrice
                    }
                  }
                  totalDiscount
                  priceAfterAppliedAgodaCash {
                    perBook {
                      ...Fragj069fae296014266j450
                    }
                    perRoomPerNight {
                      ...Fragj069fae296014266j450
                    }
                  }
                }
                apsPeek {
                  perRoomPerNight {
                    ...Fragi4ag4943ej703494628c
                  }
                }
                promotionPricePeek {
                  display {
                    perBook {
                      ...Fragi4ag4943ej703494628c
                    }
                    perRoomPerNight {
                      ...Fragi4ag4943ej703494628c
                    }
                    perNight {
                      ...Fragi4ag4943ej703494628c
                    }
                  }
                  discountType
                  promotionCodeType
                  promotionCode
                  promoAppliedOnFinalPrice
                  campaignName
                  childPromotions {
                    campaignId
                  }
                }
                promotionsCumulative {
                  promotionCumulativeType
                  amountPerBook
                  amountPerRoomPerNight
                  amountPerNight
                  amountPercentage
                  minNightsStay
                }
                channelDiscountSummary {
                  channelDiscountBreakdown {
                    channelId
                    discountPercent
                    display
                  }
                }
                packagePriceAndSaving {
                  perPax {
                    allInclusive {
                      specialPriceAndSaving {
                        baseChannel
                        targetChannel
                        targetPrice
                        saving {
                          amount
                        }
                      }
                    }
                  }
                }
              }
              discount {
                deals
                channelDiscount
              }
              saveUpTo {
                perRoomPerNight
              }
              benefits {
                id
              }
              mseRoomSummaries {
                supplierId
                subSupplierId
                pricingSummaries {
                  currency
                  price {
                    perRoomPerNight {
                      exclusive {
                        display
                      }
                      inclusive {
                        display
                      }
                    }
                  }
                }
              }
              agodaCash {
                showBadge
                giftcardGuid
                dayToEarn
                expiryDay
              }
              cashback {
                cashbackGuid
                showPostCashbackPrice
                percentage
                earnId
                dayToEarn
                expiryDay
                cashbackVersion
                cashbackType
                appliedCampaignName
              }
              corInfo {
                corBreakdown {
                  taxExPN {
                    ...Frag4e2274hj862b58988gda
                  }
                  taxInPN {
                    ...Frag4e2274hj862b58988gda
                  }
                  taxExPRPN {
                    ...Frag4e2274hj862b58988gda
                  }
                  taxInPRPN {
                    ...Frag4e2274hj862b58988gda
                  }
                }
                corInfo {
                  corType
                }
              }
              loyaltyDisplay {
                items
              }
              capacity {
                extraBedsAvailable
              }
              pricingMessages {
                formatted {
                  location
                  texts {
                    index
                    text
                  }
                }
              }
              isPackageEligible
              localVoucher {
                currencyCode
                amount
              }
              rareRoomType
              campaign {
                selected {
                  messages {
                    campaignName
                    title
                    titleWithDiscount
                    description
                    linkOutText
                    url
                  }
                }
              }
              toolTip {
                corText
              }
            }
          }
        }
        isEasyCancel
        priceChange {
          changePercentage
        }
        cheapestRoomOffer {
          uid
          corInfo {
            corBreakdown {
              taxExPRPN {
                id
                price
              }
              taxInPRPN {
                id
                price
              }
            }
          }
        }
        pulseCampaignMetadata {
          campaignBadgeText
          campaignBadgeDescText
          campaignTypeId
          promotionTypeId
          webCampaignId
          dealExpiryTime
          showPulseMerchandise
          campaignBadgeLogo
          campaignBadgeType
        }
        suggestPriceType {
          suggestPrice
        }
        growthProgramInfo {
          badges
        }
      }
      enrichment {
        topSellingPoint {
          tspType
          value
          cmsId
        }
        uniqueSellingPoint {
          rank
          segment
          uspType
          uspPropertyType
        }
        pricingBadges {
          badges
        }
        distance {
          fromUser {
            distanceM
          }
          fromLandmark {
            distanceM
          }
          fromExtraProperty {
            distanceM
          }
        }
        roomInformation {
          cheapestRoomName
          cheapestRoomSizeSqm
        }
        showReviewSnippet
      }
      metaLab {
        attributes {
          attributeId
          dataType
          value
          version
        }
      }
    }
    searchEnrichment {
      pageToken
    }
    aggregation {
      matrixGroupResults {
        matrixGroup
        matrixItemResults {
          id
          filterKey
          filterRequestType
          count
          name
          syncId
        }
      }
    }
    featuredPulseProperties(ContentSummaryRequest: $ContentSummaryRequest, PricingSummaryRequest: $PricingSummaryRequest) {
      propertyId
      propertyResultType
      pricing {
        isAvailable
        isReady
        offers {
          roomOffers {
            room {
              pricing {
                currency
                price {
                  perNight {
                    exclusive {
                      ...Fragh9a3f20iai782dhf47je
                    }
                    inclusive {
                      ...Fragh9a3f20iai782dhf47je
                    }
                  }
                  perRoomPerNight {
                    exclusive {
                      ...Fragh9a3f20iai782dhf47je
                    }
                    inclusive {
                      ...Fragh9a3f20iai782dhf47je
                    }
                  }
                }
              }
            }
          }
        }
        pulseCampaignMetadata {
          campaignTypeId
          campaignBadgeText
          campaignBadgeDescText
          dealExpiryTime
          promotionTypeId
          webCampaignId
          showPulseMerchandise
          campaignBadgeLogo
          campaignBadgeType
        }
        suggestPriceType {
          suggestPrice
        }
      }
      content {
        reviews {
          contentReview {
            isDefault
            providerId
            cumulative {
              reviewCount
              score
            }
          }
          cumulative {
            reviewCount
            score
          }
        }
        images {
          hotelImages {
            urls {
              value
            }
          }
        }
        informationSummary {
          hasHostExperience
          propertyType
          displayName
          rating
          propertyLinks {
            propertyPage
          }
          address {
            countryCode
            country {
              id
            }
            area {
              ...Fragiadej55h86afai6hji2a
            }
            city {
              ...Fragiadej55h86afai6hji2a
            }
          }
        }
      }
    }
    highlyRatedAgodaHomes(ContentSummaryRequest: $ContentSummaryRequest, PricingSummaryRequest: $PricingSummaryRequest) {
      propertyId
      propertyResultType
      pricing {
        isAvailable
        isReady
        offers {
          roomOffers {
            room {
              pricing {
                currency
                price {
                  perNight {
                    exclusive {
                      ...Fragh9a3f20iai782dhf47je
                    }
                    inclusive {
                      ...Fragh9a3f20iai782dhf47je
                    }
                  }
                  perRoomPerNight {
                    exclusive {
                      ...Fragh9a3f20iai782dhf47je
                    }
                    inclusive {
                      ...Fragh9a3f20iai782dhf47je
                    }
                  }
                }
              }
            }
          }
        }
      }
      content {
        nonHotelAccommodation {
          masterRoom {
            roomSizeSqm
            highlightedFacilities
          }
        }
        reviews {
          contentReview {
            isDefault
            providerId
            cumulative {
              reviewCount
              score
            }
          }
          cumulative {
            reviewCount
            score
          }
        }
        images {
          hotelImages {
            urls {
              value
            }
          }
        }
        informationSummary {
          hasHostExperience
          propertyType
          displayName
          rating
          propertyLinks {
            propertyPage
          }
          nhaSummary {
            hostType
          }
          address {
            countryCode
            country {
              id
            }
            area {
              ...Fragiadej55h86afai6hji2a
            }
            city {
              ...Fragiadej55h86afai6hji2a
            }
          }
        }
      }
    }
  }
}

fragment Fragj069fae296014266j450 on DisplayPrice {
  exclusive
  allInclusive
}

fragment Fragi4ag4943ej703494628c on DFDisplayPrice {
  exclusive
  allInclusive
}

fragment Frag4e2274hj862b58988gda on DFCorBreakdownItem {
  price
  id
}

fragment Fragh9a3f20iai782dhf47je on DFPrices {
  crossedOutPrice
  display
}

fragment Fragiadej55h86afai6hji2a on ContentIdName {
  name
}"""

    page_token = ""
    current_page = 1
    all_hotels = []
    seen_hotel_ids = set()
    max_retries = 3

    print(f"🚀 开始抓取 Agoda {city_name} 酒店数据...")
    print(f"📅 入住日期: {checkin}, 入住 {los} 晚, {adults} 位成人")
    print(f"📊 每页数量: {page_size}")
    print("=" * 60)

    total_hotels = None
    consecutive_empty_pages = 0
    max_consecutive_empty = 5

    while True:
        if max_pages and current_page > max_pages:
            print(f"🛑 已达到指定最大页数 {max_pages}，停止抓取。")
            break

        print(f"\n📄 正在抓取第 {current_page} 页")
        if page_token:
            print(f"   🔑 pageToken: {page_token[:50]}...")

        current_poll_id = str(uuid.uuid4())

        # 构建请求体 - 使用更符合 Agoda 实际请求的参数
        payload = {
            "operationName": "citySearch",
            "variables": {
                "CitySearchRequest": {
                    "cityId": city_id,
                    "searchRequest": {
                        "searchCriteria": {
                            "bookingDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                            "checkInDate": checkin_str,
                            "los": los,
                            "rooms": 1,
                            "adults": adults,
                            "children": 0,
                            "childAges": [],
                            "ratePlans": [1],
                            "featureFlagRequest": {
                                "fiveStarDealOfTheDay": True,
                                "isAllowBookOnRequest": False,
                                "showUnAvailable": True,
                                "showRemainingProperties": True,
                                "isMultiHotelSearch": False,
                                "enableAgencySupplyForPackages": True,
                                "flags": [
                                    {"feature": "FamilyChildFriendlyPopularFilter", "enable": True},
                                    {"feature": "FamilyChildFriendlyPropertyTypeFilter", "enable": True},
                                    {"feature": "FamilyMode", "enable": False}
                                ],
                                "isFlexibleMultiRoomSearch": False,
                                "enablePageToken": True
                            },
                            "isUserLoggedIn": False,
                            "currency": "CNY",
                            "travellerType": "Couple",
                            "isAPSPeek": False,
                            "enableOpaqueChannel": False,
                            "sorting": {"sortField": "Ranking", "sortOrder": "Desc"},
                            "requiredBasis": "PRPN",
                            "requiredPrice": "AllInclusive",
                            "suggestionLimit": 0,
                            "synchronous": False,
                            "isRoomSuggestionRequested": False,
                            "isAPORequest": False,
                            "hasAPOFilter": False,
                            "isAllowBookOnRequest": True,
                            "localCheckInDate": checkin
                        },
                        "searchContext": {
                            "searchId": search_id,
                            "userId": "2b7007b9-723c-4b53-b254-e7921da5be7d",
                            "memberId": 0,
                            "locale": "zh-cn",
                            "cid": -1,
                            "origin": "CN",
                            "platform": 4,
                            "deviceTypeId": 1,
                            "experiments": {"forceByExperiment": []},
                            "isRetry": False,
                            "showCMS": False,
                            "ipAddress": "183.6.6.101",
                            "storeFrontId": 3,
                            "pageTypeId": 103,
                            "endpointSearchType": "CitySearch",
                            "pollingInfoRequest": {
                                "pollId": current_poll_id,
                                "pollAttempt": 0
                            }
                        },
                        "filterRequest": {"idsFilters": [], "rangeFilters": [], "textFilters": []},
                        "matrixGroup": [
                            {"matrixGroup": "StarRating", "size": 100},
                            {"matrixGroup": "AccommodationType", "size": 100},
                            {"matrixGroup": "HotelAreaId", "size": 100},
                            {"matrixGroup": "HotelFacilities", "size": 100},
                            {"matrixGroup": "ReviewScore", "size": 100},
                            {"matrixGroup": "PaymentOptions", "size": 100},
                            {"matrixGroup": "RoomBenefits", "size": 100},
                            {"matrixGroup": "CityCenterDistance", "size": 100},
                            {"matrixGroup": "RoomAmenities", "size": 100},
                            {"matrixGroup": "GroupedBedTypes", "size": 100},
                            {"matrixGroup": "NumberOfBedrooms", "size": 100},
                            {"matrixGroup": "LandmarkIds", "size": 100},
                            {"matrixGroup": "ReviewLocationScore", "size": 100},
                            {"matrixGroup": "BeachAccessTypeIds", "size": 100}
                        ],
                        "page": {
                            "pageSize": page_size,
                            "pageNumber": current_page,
                            "pageToken": page_token
                        },
                        "searchHistory": [
                            {
                                "searchDate": "2026-04-29",
                                "searchType": "PropertySearch",
                                "objectId": 49409574,
                                "childrenAges": []
                            }
                        ],
                        "isTrimmedResponseRequested": False,
                        "extraHotels": {"extraHotelIds": [], "enableFiltersForExtraHotels": False},
                        "highlyRatedAgodaHomesRequest": {
                            "numberOfAgodaHomes": 30,
                            "minimumReviewScore": 7.5,
                            "minimumReviewCount": 3,
                            "accommodationTypes": [28, 29, 30, 102, 103, 106, 107, 108, 109, 110, 114, 115, 120, 131],
                            "sortVersion": 0
                        },
                        "featuredPulsePropertiesRequest": {"numberOfPulseProperties": 15},
                        "rankingRequest": {"isNhaKeywordSearch": False, "isPulseRankingBoost": False},
                        "searchDetailRequest": {"priceHistogramBins": 30}
                    }
                },
                "ContentSummaryRequest": {
                    "context": {
                        "rawUserId": "2b7007b9-723c-4b53-b254-e7921da5be7d",
                        "memberId": 0,
                        "userOrigin": "CN",
                        "locale": "zh-cn",
                        "forceExperimentsByIdNew": [],
                        "apo": False,
                        "searchCriteria": {"cityId": city_id},
                        "platform": {"id": 4},
                        "cid": "-1",
                        "storeFrontId": 3,
                        "occupancy": {
                            "numberOfAdults": adults,
                            "numberOfChildren": 0,
                            "travelerType": 1,
                            "checkIn": checkin_str
                        },
                        "deviceTypeId": 1,
                        "whiteLabelKey": "",
                        "correlationId": ""
                    },
                    "summary": {"includeHotelCharacter": False},
                    "rateCategories": True,
                    "contentRateCategories": {"escapeRateCategories": {}},
                    "reviews": {
                        "demographics": {"filter": {"defaultProviderOnly": True}},
                        "summaries": {"apo": True, "limit": 1, "travellerType": 1},
                        "cumulative": {}
                    },
                    "images": {
                        "page": {"pageNumber": 1, "pageSize": 3},
                        "maxWidth": 0,
                        "maxHeight": 0,
                        "imageSizes": [
                            {"key": "normal", "size": {"width": 167, "height": 85}},
                            {"key": "retina", "size": {"width": 334, "height": 170}}
                        ]
                    },
                    "nonHotelAccommodation": False,
                    "engagement": True,
                    "highlights": {"includeCollection": False}
                },
                "PricingSummaryRequest": {
                    "cheapestOnly": True,
                    "context": {
                        "abTests": [
                            {"testId": 9021, "abUser": "B"},
                            {"testId": 9023, "abUser": "B"},
                            {"testId": 9024, "abUser": "B"},
                            {"testId": 9025, "abUser": "B"},
                            {"testId": 9027, "abUser": "B"},
                            {"testId": 9029, "abUser": "B"}
                        ],
                        "clientInfo": {
                            "cid": -1,
                            "languageId": 8,
                            "ipAddress": "183.6.6.101",
                            "languageUse": 1,
                            "origin": "CN",
                            "platform": 4,
                            "searchId": search_id,
                            "storefront": 3,
                            "userId": "2b7007b9-723c-4b53-b254-e7921da5be7d"
                        },
                        "experiment": [
                            {"name": "JGCW-264", "variant": "B"},
                            {"name": "JGCW-204", "variant": "B"}
                        ],
                        "isAllowBookOnRequest": True,
                        "sessionInfo": {"isLogin": False, "memberId": 0, "sessionId": 1},
                        "pollingInfoRequest": {
                            "pollId": current_poll_id,
                            "pollAttempt": 0
                        }
                    },
                    "roomSortingStrategy": None,
                    "isSSR": True,
                    "pricing": {
                        "bookingDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                        "checkIn": checkin_str,
                        "checkout": checkout_date.strftime("%Y-%m-%dT00:00:00.000Z"),
                        "currency": "CNY",
                        "details": {"cheapestPriceOnly": False, "itemBreakdown": False, "priceBreakdown": False},
                        "featureFlag": [
                            "ClientDiscount", "VipPlatinum", "VipDiamond", "Coupon",
                            "CreditCardPromotionPeek", "EnableCashback", "DispatchGoLocalForInternational",
                            "EnableGoToTravelCampaign", "EnableCofundedCashback", "EnableCashbackMildlyAggressiveDisplay",
                            "AutoApplyPromos", "EnableAgencySupplyForPackages", "MixAndSave",
                            "ReturnHotelNotReadyIfPullNotReady", "APSPeek", "PromosCumulative",
                            "DomesticTaxReceipt", "QuantumPaymentsEnabled"
                        ],
                        "features": {
                            "crossOutRate": False,
                            "isAPSPeek": False,
                            "isAllOcc": False,
                            "isApsEnabled": False,
                            "isIncludeUsdAndLocalCurrency": False,
                            "isMSE": True,
                            "isRPM2Included": True,
                            "maxSuggestions": 0,
                            "newRateModel": False,
                            "overrideOccupancy": False,
                            "priusId": 0,
                            "synchronous": False,
                            "filterCheapestRoomEscapesPackage": False,
                            "calculateRareRoomBadge": True,
                            "enableRichContentOffer": True,
                            "enablePushDayUseRates": True,
                            "returnCheapestEscapesOfferOnSSR": True,
                            "enableEscapesPackage": True,
                            "disableEscapesPackage": False,
                            "isEnableSupplierFinancialInfo": False,
                            "isLoggingAuctionData": False,
                            "enableRatePlanCheckInCheckOut": True,
                            "enableSuggestPriceExclusiveWithFees": True
                        },
                        "filters": {
                            "cheapestRoomFilters": [],
                            "filterAPO": False,
                            "ratePlans": [1],
                            "secretDealOnly": False,
                            "suppliers": []
                        },
                        "includedPriceInfo": False,
                        "localCheckInDate": checkin,
                        "localCheckoutDate": checkout_date.strftime("%Y-%m-%d"),
                        "occupancy": {
                            "adults": adults,
                            "children": 0,
                            "rooms": 1,
                            "childAges": [],
                            "childrenTypes": []
                        },
                        "supplierPullMetadata": {"requiredPrecheckAccuracyLevel": 0},
                        "mseHotelIds": [],
                        "mseClicked": "",
                        "bookingDurationType": None,
                        "ppLandingHotelIds": [],
                        "searchedHotelIds": [],
                        "paymentId": -1
                    },
                    "suggestedPrice": "NA"
                },
                "PriceStreamMetaLabRequest": {"attributesId": [2, 3, 1, 8, 6]}
            },
            "query": graphql_query
        }

        # 发送请求
        data = None
        for retry in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                print(f"   📡 响应状态码: {response.status_code}")

                if response.status_code == 429:
                    print(f"   ⚠️ 请求过于频繁，等待 10 秒后重试...")
                    time.sleep(10)
                    continue

                if response.status_code != 200:
                    print(f"   ❌ 请求失败: {response.status_code}")
                    if retry < max_retries - 1:
                        time.sleep(5)
                        continue
                    break

                data = response.json()

                if "errors" in data:
                    print(f"   ❌ GraphQL 错误: {data['errors'][0].get('message', 'Unknown')[:100]}")
                    if retry < max_retries - 1:
                        time.sleep(5)
                        continue
                    break

                break

            except Exception as e:
                print(f"   ❌ 请求异常: {e}")
                if retry < max_retries - 1:
                    time.sleep(5)
                    continue
                break

        if data is None:
            print(f"❌ 第 {current_page} 页请求失败，停止抓取")
            break

        city_search = data.get("data", {}).get("citySearch", {})

        # 处理轮询
        search_result = city_search.get("searchResult", {})
        search_info = search_result.get("searchInfo", {})
        polling_info = search_info.get("pollingInfoResponse", {})

        # 获取总酒店数
        if total_hotels is None:
            total_hotels = search_info.get("totalActiveHotels", 0)
            if total_hotels:
                print(f"   📊 总酒店数: {total_hotels}")

        # 处理轮询逻辑
        properties = city_search.get("properties", [])
        poll_attempt = 0
        max_poll_attempts = 15

        while polling_info and polling_info.get("shouldPoll", False) and poll_attempt < max_poll_attempts:
            if properties:
                # 已经有数据了
                break

            wait_time = polling_info.get('suggestedPollIntervalMs', 2000) / 1000
            poll_attempt += 1
            print(f"   ⏳ 轮询第 {poll_attempt}/{max_poll_attempts} 次，等待 {wait_time} 秒...")
            time.sleep(wait_time)

            # 更新轮询参数
            payload["variables"]["CitySearchRequest"]["searchRequest"]["searchContext"]["pollingInfoRequest"]["pollAttempt"] = poll_attempt
            payload["variables"]["PricingSummaryRequest"]["context"]["pollingInfoRequest"]["pollAttempt"] = poll_attempt

            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    if "errors" not in data:
                        city_search = data.get("data", {}).get("citySearch", {})
                        search_result = city_search.get("searchResult", {})
                        search_info = search_result.get("searchInfo", {})
                        polling_info = search_info.get("pollingInfoResponse", {})
                        properties = city_search.get("properties", [])
                        if properties:
                            print(f"   ✅ 轮询完成，获取到 {len(properties)} 条数据")
                            break
            except Exception as e:
                print(f"   ⚠️ 轮询请求异常: {e}")

        if not properties:
            # 检查是否真的没有数据
            if total_hotels and len(all_hotels) >= total_hotels:
                print(f"🏁 已抓取所有 {total_hotels} 家酒店")
                break

            consecutive_empty_pages += 1
            print(f"   ⚠️ 本页无数据，连续空页: {consecutive_empty_pages}")

            if consecutive_empty_pages >= max_consecutive_empty:
                print(f"🏁 连续 {max_consecutive_empty} 页无数据，停止抓取")
                break

            current_page += 1
            continue

        consecutive_empty_pages = 0

        # 解析数据
        page_count = 0
        for prop in properties:
            if prop.get("propertyResultType") != "NormalProperty":
                continue

            prop_id = prop.get("propertyId")
            if prop_id in seen_hotel_ids:
                continue
            seen_hotel_ids.add(prop_id)

            content = prop.get("content", {})
            info = content.get("informationSummary", {})

            name = info.get("localeName") or info.get("displayName") or info.get("defaultName")
            if not name:
                continue

            addr = info.get("address", {})
            area = addr.get("area", {}).get("name", "")
            city = addr.get("city", {}).get("name", "")

            reviews = content.get("reviews", {})
            cum = reviews.get("cumulative")

            if cum and isinstance(cum, dict):
                rating = cum.get("score")
                review_cnt = cum.get("reviewCount", 0)
            else:
                rating = None
                review_cnt = 0

            star = info.get("rating", 0)
            if star == 0:
                star = None

            # 提取价格
            pricing = prop.get("pricing", {})
            price = 0
            offers = pricing.get("offers", [])
            if offers:
                for offer in offers:
                    room_offers = offer.get("roomOffers", [])
                    for room_offer in room_offers:
                        room = room_offer.get("room", {})
                        pricing_data = room.get("pricing", [])
                        if pricing_data and isinstance(pricing_data, list) and len(pricing_data) > 0:
                            per_room = pricing_data[0].get("price", {}).get("perRoomPerNight", {})
                            exclusive = per_room.get("exclusive", {})
                            price = exclusive.get("display", 0)
                            if price:
                                break
                    if price:
                        break

            all_hotels.append({
                "酒店ID": prop_id,
                "酒店名称": name,
                "地址": f"{area} {city}".strip(),
                "区域": area,
                "Agoda评分": rating,
                "评价数": review_cnt,
                "星级": star,
                "最低价(CNY)": price if price > 0 else None,
                "可订状态": "可订" if pricing.get("isAvailable") else "已售罄"
            })
            page_count += 1

        print(f"   ✅ 本页新增: {page_count} 家 | 累计: {len(all_hotels)}")
        if total_hotels and total_hotels > 0:
            percentage = len(all_hotels) / total_hotels * 100
            print(f"   📊 进度: {len(all_hotels)}/{total_hotels} ({percentage:.2f}%)")

        # 检查是否完成
        if total_hotels and len(all_hotels) >= total_hotels:
            print(f"🏁 已抓取所有 {total_hotels} 家酒店")
            break

        # 获取下一页 token
        search_enrichment = city_search.get("searchEnrichment", {})
        next_page_token = search_enrichment.get("pageToken", "")

        # 判断是否还有下一页
        if not next_page_token:
            print("🏁 没有更多分页数据 (pageToken 为空)")
            break

        if next_page_token == page_token:
            # pageToken 相同，可能需要使用 pageNumber 递增
            print(f"   ⚠️ pageToken 未变化，尝试使用 pageNumber 分页")
            # 继续使用 pageNumber 递增
        else:
            print(f"   🔑 新 pageToken: {next_page_token[:30]}...")

        page_token = next_page_token
        current_page += 1

        # 添加延迟
        time.sleep(1.5)

    # 保存结果
    if all_hotels:
        df = pd.DataFrame(all_hotels)

        filename = f"Agoda_{city_name}_酒店_{checkin}.xlsx"
        df.to_excel(filename, index=False, engine='openpyxl')

        print("\n" + "=" * 60)
        print(f"🎉 完成！共抓取 {len(df)} 家酒店")
        print(f"💾 保存到: {filename}")
        print("=" * 60)

        if len(df) > 0:
            df_with_score = df[df["Agoda评分"].notna()]
            df_with_price = df[df["最低价(CNY)"].notna()]

            if len(df_with_score) > 0:
                avg_score = df_with_score["Agoda评分"].mean()
                print(f"\n📊 平均评分: {avg_score:.1f} (基于 {len(df_with_score)} 家有评分的酒店)")

            if len(df_with_price) > 0:
                avg_price = df_with_price["最低价(CNY)"].mean()
                print(f"💰 平均最低价: ¥{avg_price:.2f} (基于 {len(df_with_price)} 家有价格的酒店)")

            print(f"\n🏆 评分前10名:")
            top10 = df.nlargest(10, "Agoda评分") if len(df_with_score) > 0 else df.head(10)
            for i, row in top10.head(10).iterrows():
                name_short = row['酒店名称'][:35] if len(row['酒店名称']) > 35 else row['酒店名称']
                price_str = f"¥{row['最低价(CNY)']:.2f}" if row['最低价(CNY)'] else "无价格"
                score_str = f"{row['Agoda评分']:.1f}" if row['Agoda评分'] and row['Agoda评分'] > 0 else "暂无"
                star_str = f"{int(row['星级'])}星" if row['星级'] and row['星级'] > 0 else ""
                print(f"   {int(row['酒店ID'])} | {name_short} | {star_str} 评分: {score_str} | {price_str}")
    else:
        print("\n❌ 未抓取到数据")


if __name__ == '__main__':
    run(
        max_pages=None,
        city_id=5818,
        city_name="武汉",
        checkin="2026-06-01",
        los=1,
        adults=2,
        page_size=25
    )