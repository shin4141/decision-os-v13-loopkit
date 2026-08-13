#import <Foundation/Foundation.h>
#import <OpenDirectory/OpenDirectory.h>

#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>

#if defined(F01_MUTATION_ENABLED)
#error "This read-only qualification source cannot be compiled with mutation support."
#endif

static NSString *const F01Schema = @"decision-os-f01-slice4a-opendirectory-readonly-v0.1";
static NSString *const F01SelfTestSchema = @"decision-os-f01-slice4a-opendirectory-self-test-v0.1";
static NSString *const F01ErrorDomain = @"DecisionOS.F01.OpenDirectoryReadOnly";
static NSString *const F01NodeName = @"/Local/Default";
static NSString *const F01PrincipalName = @"_decisionos_codex";
static NSString *const F01GuardianName = @"_decisionos_guardian";
static NSString *const F01BrokerName = @"_decisionos_broker";
static NSString *const F01UserGUID = @"D6515614-B56A-4943-AA41-18D17DE9F899";
static NSString *const F01GroupGUID = @"1F200679-B0A2-4D13-A86F-6492F9C4B66F";
static NSString *const F01NumericID = @"510";
static NSString *const F01RealName = @"Decision OS Codex execution principal";
static NSString *const F01Home = @"/var/empty";
static NSString *const F01NativeIsHidden = @"dsAttrTypeNative:IsHidden";
static NSString *const F01NativeAccountPolicyData = @"dsAttrTypeNative:accountPolicyData";
static NSString *const F01NativeRecordDaemonVersion = @"dsAttrTypeNative:record_daemon_version";

static const BOOL PRIVILEGED_EXECUTION_AUTHORIZED = NO;

static NSArray<NSString *> *F01HostStatePaths(void) {
    return @[
        @"/Library/Application Support/DecisionOS",
        @"/Library/Application Support/DecisionOS/F01PrincipalSeparation",
        @"/Library/Application Support/DecisionOS/F01PrincipalSeparation/v1",
    ];
}

static NSError *F01Error(NSInteger code, NSString *description, NSDictionary *details) {
    NSMutableDictionary *userInfo = [NSMutableDictionary dictionaryWithDictionary:details ?: @{}];
    userInfo[NSLocalizedDescriptionKey] = description;
    return [NSError errorWithDomain:F01ErrorDomain code:code userInfo:userInfo];
}

static id F01CanonicalValue(id value) {
    if (value == nil || value == [NSNull null]) {
        return [NSNull null];
    }
    if ([value isKindOfClass:[NSString class]] ||
        [value isKindOfClass:[NSNumber class]]) {
        return value;
    }
    if ([value isKindOfClass:[NSData class]]) {
        return @{ @"data_base64": [(NSData *)value base64EncodedStringWithOptions:0] };
    }
    if ([value isKindOfClass:[NSArray class]]) {
        NSMutableArray *result = [NSMutableArray array];
        for (id item in (NSArray *)value) {
            [result addObject:F01CanonicalValue(item)];
        }
        return result;
    }
    if ([value isKindOfClass:[NSDictionary class]]) {
        NSMutableDictionary *result = [NSMutableDictionary dictionary];
        for (id rawKey in (NSDictionary *)value) {
            NSString *key = [rawKey isKindOfClass:[NSString class]]
                ? rawKey
                : [rawKey description];
            result[key] = F01CanonicalValue(((NSDictionary *)value)[rawKey]);
        }
        return result;
    }
    return @{ @"description": [value description],
              @"objective_c_class": NSStringFromClass([value class]) };
}

static NSDictionary *F01ErrorEvidence(NSError *error) {
    return @{
        @"code": @(error.code),
        @"domain": error.domain ?: @"",
        @"localized_description": error.localizedDescription ?: @"",
        @"localized_failure_reason": error.localizedFailureReason ?: [NSNull null],
        @"localized_recovery_suggestion": error.localizedRecoverySuggestion ?: [NSNull null],
        @"user_info": F01CanonicalValue(error.userInfo ?: @{}),
    };
}

static NSData *F01CanonicalJSON(id object, NSError **error) {
    NSData *body = [NSJSONSerialization dataWithJSONObject:object
                                                   options:(NSJSONWritingSortedKeys |
                                                            NSJSONWritingWithoutEscapingSlashes)
                                                     error:error];
    if (body == nil) {
        return nil;
    }
    NSMutableData *line = [body mutableCopy];
    const uint8_t newline = '\n';
    [line appendBytes:&newline length:1];
    return line;
}

static BOOL F01WriteJSON(id object) {
    NSError *error = nil;
    NSData *data = F01CanonicalJSON(object, &error);
    if (data == nil) {
        fprintf(stderr, "canonical JSON failure: %s\n", error.localizedDescription.UTF8String);
        return NO;
    }
    return fwrite(data.bytes, 1, data.length, stdout) == data.length;
}

static NSArray *F01Query(ODNode *node,
                         NSString *recordType,
                         NSString *attribute,
                         NSString *value,
                         id returnAttributes,
                         NSError **error) {
    ODQuery *query = [ODQuery queryWithNode:node
                            forRecordTypes:recordType
                                 attribute:attribute
                                 matchType:kODMatchEqualTo
                               queryValues:value
                          returnAttributes:returnAttributes
                            maximumResults:2
                                     error:error];
    if (query == nil) {
        return nil;
    }
    return [query resultsAllowingPartial:NO error:error];
}

static NSDictionary *F01NormalizeAttributes(NSDictionary *details,
                                             NSMutableArray<NSString *> *errors) {
    NSMutableDictionary *normalized = [NSMutableDictionary dictionary];
    for (id rawKey in details) {
        if (![rawKey isKindOfClass:[NSString class]]) {
            [errors addObject:@"OpenDirectory returned a non-string attribute key."];
            continue;
        }
        id rawValues = details[rawKey];
        if (![rawValues isKindOfClass:[NSArray class]]) {
            [errors addObject:[NSString stringWithFormat:
                @"OpenDirectory attribute %@ did not contain an array.", rawKey]];
            normalized[rawKey] = F01CanonicalValue(rawValues);
            continue;
        }
        NSMutableArray *values = [NSMutableArray array];
        for (id value in (NSArray *)rawValues) {
            if (![value isKindOfClass:[NSString class]] &&
                ![value isKindOfClass:[NSData class]]) {
                [errors addObject:[NSString stringWithFormat:
                    @"OpenDirectory attribute %@ contained unsupported value type %@.",
                    rawKey, NSStringFromClass([value class])]];
            }
            [values addObject:F01CanonicalValue(value)];
        }
        [values sortUsingComparator:^NSComparisonResult(id left, id right) {
            NSData *leftJSON = [NSJSONSerialization dataWithJSONObject:left
                                                                 options:(NSJSONWritingSortedKeys |
                                                                          NSJSONWritingFragmentsAllowed)
                                                                   error:NULL];
            NSData *rightJSON = [NSJSONSerialization dataWithJSONObject:right
                                                                  options:(NSJSONWritingSortedKeys |
                                                                           NSJSONWritingFragmentsAllowed)
                                                                    error:NULL];
            NSString *leftKey = leftJSON == nil
                ? [left description]
                : [[NSString alloc] initWithData:leftJSON encoding:NSUTF8StringEncoding];
            NSString *rightKey = rightJSON == nil
                ? [right description]
                : [[NSString alloc] initWithData:rightJSON encoding:NSUTF8StringEncoding];
            return [leftKey compare:rightKey options:NSLiteralSearch];
        }];
        normalized[rawKey] = values;
    }
    return normalized;
}

static NSDictionary *F01RecordObservation(ODRecord *record, NSError **error) {
    NSDictionary *details = [record recordDetailsForAttributes:@[kODAttributeTypeAllAttributes]
                                                          error:error];
    if (details == nil) {
        return nil;
    }
    NSMutableArray<NSString *> *normalizationErrors = [NSMutableArray array];
    return @{
        @"attributes": F01NormalizeAttributes(details, normalizationErrors),
        @"framework_record_name": record.recordName ?: [NSNull null],
        @"framework_record_type": record.recordType ?: [NSNull null],
        @"normalization_errors": normalizationErrors,
    };
}

static NSDictionary *F01TargetRecord(ODNode *node,
                                     NSString *recordType,
                                     NSError **error) {
    NSArray *records = F01Query(node,
                                recordType,
                                kODAttributeTypeRecordName,
                                F01PrincipalName,
                                kODAttributeTypeAllAttributes,
                                error);
    if (records == nil) {
        return nil;
    }
    NSMutableDictionary *result = [@{ @"match_count": @(records.count) } mutableCopy];
    if (records.count == 1) {
        id candidate = records.firstObject;
        if (![candidate isKindOfClass:[ODRecord class]]) {
            if (error != NULL) {
                *error = F01Error(20, @"OpenDirectory returned a non-record result.", @{});
            }
            return nil;
        }
        NSDictionary *observation = F01RecordObservation(candidate, error);
        if (observation == nil) {
            return nil;
        }
        [result addEntriesFromDictionary:observation];
    } else {
        result[@"attributes"] = @{};
        result[@"framework_record_name"] = [NSNull null];
        result[@"framework_record_type"] = [NSNull null];
        result[@"normalization_errors"] = @[];
    }
    return result;
}

static NSArray<NSString *> *F01RecordNames(ODNode *node,
                                           NSString *recordType,
                                           NSString *attribute,
                                           NSString *value,
                                           NSError **error) {
    NSArray *records = F01Query(node,
                                recordType,
                                attribute,
                                value,
                                @[kODAttributeTypeRecordName],
                                error);
    if (records == nil) {
        return nil;
    }
    NSMutableArray<NSString *> *names = [NSMutableArray array];
    for (id candidate in records) {
        if (![candidate isKindOfClass:[ODRecord class]]) {
            if (error != NULL) {
                *error = F01Error(21, @"OpenDirectory returned a non-record result.", @{});
            }
            return nil;
        }
        NSString *name = ((ODRecord *)candidate).recordName;
        if (name == nil) {
            if (error != NULL) {
                *error = F01Error(22, @"OpenDirectory returned a record without a name.", @{});
            }
            return nil;
        }
        [names addObject:name];
    }
    [names sortUsingSelector:@selector(compare:)];
    return names;
}

static BOOL F01PathPresent(NSString *path, NSError **error) {
    struct stat status;
    if (lstat(path.fileSystemRepresentation, &status) == 0) {
        return YES;
    }
    if (errno == ENOENT) {
        return NO;
    }
    if (error != NULL) {
        *error = [NSError errorWithDomain:NSPOSIXErrorDomain
                                     code:errno
                                 userInfo:@{
                                     NSFilePathErrorKey: path,
                                     NSLocalizedDescriptionKey:
                                         [NSString stringWithFormat:
                                             @"Cannot inspect host-state path %@: %s",
                                             path, strerror(errno)],
                                 }];
    }
    return NO;
}

static __attribute__((unused)) NSDictionary *F01ObserveHost(NSError **error) {
    ODNode *node = [ODNode nodeWithSession:[ODSession defaultSession]
                                     name:F01NodeName
                                    error:error];
    if (node == nil) {
        return nil;
    }

    NSDictionary *user = F01TargetRecord(node, kODRecordTypeUsers, error);
    if (user == nil) {
        return nil;
    }
    NSDictionary *group = F01TargetRecord(node, kODRecordTypeGroups, error);
    if (group == nil) {
        return nil;
    }
    NSArray *uidNames = F01RecordNames(node,
                                       kODRecordTypeUsers,
                                       kODAttributeTypeUniqueID,
                                       F01NumericID,
                                       error);
    if (uidNames == nil) {
        return nil;
    }
    NSArray *gidNames = F01RecordNames(node,
                                       kODRecordTypeGroups,
                                       kODAttributeTypePrimaryGroupID,
                                       F01NumericID,
                                       error);
    if (gidNames == nil) {
        return nil;
    }

    NSMutableDictionary *held = [NSMutableDictionary dictionary];
    for (NSString *recordType in @[kODRecordTypeUsers, kODRecordTypeGroups]) {
        NSString *kind = [recordType isEqualToString:kODRecordTypeUsers] ? @"user" : @"group";
        for (NSString *name in @[F01GuardianName, F01BrokerName]) {
            NSArray *matches = F01RecordNames(node,
                                              recordType,
                                              kODAttributeTypeRecordName,
                                              name,
                                              error);
            if (matches == nil) {
                return nil;
            }
            NSString *principal = [name isEqualToString:F01GuardianName] ? @"guardian" : @"broker";
            held[[NSString stringWithFormat:@"%@_%@", principal, kind]] = matches;
        }
    }

    NSMutableDictionary *paths = [NSMutableDictionary dictionary];
    for (NSString *path in F01HostStatePaths()) {
        NSError *pathError = nil;
        BOOL present = F01PathPresent(path, &pathError);
        if (pathError != nil) {
            if (error != NULL) {
                *error = pathError;
            }
            return nil;
        }
        paths[path] = @(present);
    }

    return @{
        @"execution": @{
            @"effective_uid": @(geteuid()),
            @"mutation_attempted": @(NO),
            @"privileged_execution_authorized": @(PRIVILEGED_EXECUTION_AUTHORIZED),
        },
        @"held_principals": held,
        @"host_state_paths_present": paths,
        @"node": @{
            @"requested": F01NodeName,
            @"resolved": node.nodeName ?: [NSNull null],
        },
        @"numeric_bindings": @{
            @"gid_510_record_names": gidNames,
            @"uid_510_record_names": uidNames,
        },
        @"records": @{
            @"group": group,
            @"user": user,
        },
    };
}

static NSArray *F01Values(NSDictionary *record, NSString *attribute) {
    id attributes = record[@"attributes"];
    if (![attributes isKindOfClass:[NSDictionary class]]) {
        return nil;
    }
    id values = ((NSDictionary *)attributes)[attribute];
    return [values isKindOfClass:[NSArray class]] ? values : nil;
}

static void F01RequireValues(NSMutableArray<NSString *> *issues,
                             NSDictionary *record,
                             NSString *attribute,
                             NSArray *expected,
                             NSString *label) {
    NSArray *actual = F01Values(record, attribute);
    if (actual == nil || ![actual isEqualToArray:expected]) {
        [issues addObject:[NSString stringWithFormat:@"%@ mismatch.", label]];
    }
}

static void F01RequireAbsent(NSMutableArray<NSString *> *issues,
                             NSDictionary *record,
                             NSString *attribute,
                             NSString *label) {
    if (F01Values(record, attribute) != nil) {
        [issues addObject:[NSString stringWithFormat:@"%@ must be absent.", label]];
    }
}

static void F01RequireExactAttributeSurface(NSMutableArray<NSString *> *issues,
                                            NSDictionary *record,
                                            NSSet<NSString *> *allowed,
                                            NSString *label) {
    NSDictionary *attributes = record[@"attributes"];
    if (![attributes isKindOfClass:[NSDictionary class]]) {
        [issues addObject:[NSString stringWithFormat:@"%@ attributes are malformed.", label]];
        return;
    }
    NSMutableSet *unexpected = [NSMutableSet setWithArray:attributes.allKeys];
    [unexpected minusSet:allowed];
    if (unexpected.count > 0) {
        NSArray *ordered = [unexpected.allObjects sortedArrayUsingSelector:@selector(compare:)];
        [issues addObject:[NSString stringWithFormat:
            @"%@ exposes unreviewed attributes: %@.", label,
            [ordered componentsJoinedByString:@", "]]];
    }
}

static void F01RequireSafeAccountPolicy(NSMutableArray<NSString *> *issues,
                                        NSDictionary *user) {
    NSArray *values = F01Values(user, F01NativeAccountPolicyData);
    if (values == nil) {
        return;
    }
    if (values.count != 1 ||
        ![values.firstObject isKindOfClass:[NSDictionary class]] ||
        ![((NSDictionary *)values.firstObject)[@"data_base64"] isKindOfClass:[NSString class]]) {
        [issues addObject:@"User accountPolicyData is malformed."];
        return;
    }
    NSData *data = [[NSData alloc]
        initWithBase64EncodedString:((NSDictionary *)values.firstObject)[@"data_base64"]
                           options:0];
    NSError *error = nil;
    id plist = data == nil ? nil : [NSPropertyListSerialization propertyListWithData:data
                                                                             options:0
                                                                              format:NULL
                                                                               error:&error];
    if (![plist isKindOfClass:[NSDictionary class]]) {
        [issues addObject:[NSString stringWithFormat:
            @"User accountPolicyData is not a dictionary plist%@.",
            error == nil ? @"" : [NSString stringWithFormat:@" (%@/%ld)",
                                  error.domain, (long)error.code]]];
        return;
    }
    NSSet *keys = [NSSet setWithArray:((NSDictionary *)plist).allKeys];
    if (![keys isSubsetOfSet:[NSSet setWithObject:@"creationTime"]]) {
        NSArray *ordered = [keys.allObjects sortedArrayUsingSelector:@selector(compare:)];
        [issues addObject:[NSString stringWithFormat:
            @"User accountPolicyData contains unreviewed policy keys: %@.",
            [ordered componentsJoinedByString:@", "]]];
    }
    id creationTime = ((NSDictionary *)plist)[@"creationTime"];
    if (creationTime != nil && ![creationTime isKindOfClass:[NSNumber class]]) {
        [issues addObject:@"User accountPolicyData creationTime is malformed."];
    }
}

static NSArray<NSString *> *F01ValidateSnapshot(NSDictionary *snapshot) {
    NSMutableArray<NSString *> *issues = [NSMutableArray array];
    NSDictionary *execution = snapshot[@"execution"];
    if (![execution[@"privileged_execution_authorized"] isEqual:@(NO)]) {
        [issues addObject:@"Privileged execution must be disabled."];
    }
    if (![execution[@"mutation_attempted"] isEqual:@(NO)]) {
        [issues addObject:@"Mutation must not be attempted."];
    }
    NSNumber *euid = execution[@"effective_uid"];
    if (![euid isKindOfClass:[NSNumber class]] || euid.unsignedIntegerValue == 0) {
        [issues addObject:@"Read-only host qualification must run unprivileged."];
    }

    NSDictionary *node = snapshot[@"node"];
    if (![node[@"requested"] isEqual:F01NodeName] ||
        ![node[@"resolved"] isEqual:F01NodeName]) {
        [issues addObject:@"OpenDirectory node must be exactly /Local/Default."];
    }

    NSDictionary *records = snapshot[@"records"];
    NSDictionary *user = records[@"user"];
    NSDictionary *group = records[@"group"];
    if (![user[@"match_count"] isEqual:@1]) {
        [issues addObject:@"User record name must resolve uniquely."];
    }
    if (![group[@"match_count"] isEqual:@1]) {
        [issues addObject:@"Group record name must resolve uniquely."];
    }
    if (![user[@"normalization_errors"] isEqual:@[]]) {
        [issues addObject:@"User record normalization failed."];
    }
    if (![group[@"normalization_errors"] isEqual:@[]]) {
        [issues addObject:@"Group record normalization failed."];
    }
    if (![user[@"framework_record_name"] isEqual:F01PrincipalName] ||
        ![user[@"framework_record_type"] isEqual:kODRecordTypeUsers]) {
        [issues addObject:@"Framework user record identity mismatch."];
    }
    if (![group[@"framework_record_name"] isEqual:F01PrincipalName] ||
        ![group[@"framework_record_type"] isEqual:kODRecordTypeGroups]) {
        [issues addObject:@"Framework group record identity mismatch."];
    }

    F01RequireValues(issues, user, kODAttributeTypeRecordName,
                     @[F01PrincipalName], @"User RecordName");
    F01RequireValues(issues, user, kODAttributeTypeUniqueID,
                     @[F01NumericID], @"User UniqueID");
    F01RequireValues(issues, user, kODAttributeTypeGUID,
                     @[F01UserGUID], @"User GeneratedUID");
    F01RequireValues(issues, user, kODAttributeTypePrimaryGroupID,
                     @[F01NumericID], @"User PrimaryGroupID");
    F01RequireValues(issues, user, kODAttributeTypeFullName,
                     @[F01RealName], @"User RealName");
    F01RequireValues(issues, user, kODAttributeTypeNFSHomeDirectory,
                     @[F01Home], @"User NFSHomeDirectory");
    F01RequireAbsent(issues, user, kODAttributeTypeUserShell, @"UserShell");
    F01RequireAbsent(issues, user, F01NativeIsHidden, @"IsHidden");
    F01RequireAbsent(issues, user, kODAttributeTypeAuthenticationAuthority,
                     @"AuthenticationAuthority");

    F01RequireValues(issues, group, kODAttributeTypeRecordName,
                     @[F01PrincipalName], @"Group RecordName");
    F01RequireValues(issues, group, kODAttributeTypePrimaryGroupID,
                     @[F01NumericID], @"Group PrimaryGroupID");
    F01RequireValues(issues, group, kODAttributeTypeGUID,
                     @[F01GroupGUID], @"Group GeneratedUID");
    F01RequireValues(issues, group, kODAttributeTypeFullName,
                     @[F01RealName], @"Group RealName");
    F01RequireAbsent(issues, group, kODAttributeTypeGroupMembership,
                     @"GroupMembership");
    F01RequireAbsent(issues, group, kODAttributeTypeGroupMembers,
                     @"GroupMembers");

    NSSet *userAllowed = [NSSet setWithArray:@[
        kODAttributeTypeRecordName,
        kODAttributeTypeUniqueID,
        kODAttributeTypeGUID,
        kODAttributeTypePrimaryGroupID,
        kODAttributeTypeFullName,
        kODAttributeTypeNFSHomeDirectory,
        kODAttributeTypeUserShell,
        F01NativeIsHidden,
        kODAttributeTypeAuthenticationAuthority,
        kODAttributeTypeRecordType,
        kODAttributeTypeMetaNodeLocation,
        kODAttributeTypePassword,
        F01NativeAccountPolicyData,
        F01NativeRecordDaemonVersion,
    ]];
    NSSet *groupAllowed = [NSSet setWithArray:@[
        kODAttributeTypeRecordName,
        kODAttributeTypePrimaryGroupID,
        kODAttributeTypeGUID,
        kODAttributeTypeFullName,
        kODAttributeTypeGroupMembership,
        kODAttributeTypeGroupMembers,
        kODAttributeTypeRecordType,
        kODAttributeTypeMetaNodeLocation,
        kODAttributeTypePassword,
        F01NativeRecordDaemonVersion,
    ]];
    F01RequireExactAttributeSurface(issues, user, userAllowed, @"User");
    F01RequireExactAttributeSurface(issues, group, groupAllowed, @"Group");
    F01RequireValues(issues, user, kODAttributeTypeRecordType,
                     @[kODRecordTypeUsers], @"User framework RecordType");
    F01RequireValues(issues, group, kODAttributeTypeRecordType,
                     @[kODRecordTypeGroups], @"Group framework RecordType");
    F01RequireValues(issues, user, kODAttributeTypeMetaNodeLocation,
                     @[F01NodeName], @"User framework node location");
    F01RequireValues(issues, group, kODAttributeTypeMetaNodeLocation,
                     @[F01NodeName], @"Group framework node location");
    F01RequireValues(issues, user, kODAttributeTypePassword,
                     @[@"********"], @"User non-credential password marker");
    F01RequireValues(issues, group, kODAttributeTypePassword,
                     @[@"*"], @"Group non-credential password marker");
    F01RequireSafeAccountPolicy(issues, user);

    NSDictionary *bindings = snapshot[@"numeric_bindings"];
    if (![bindings[@"uid_510_record_names"] isEqual:@[F01PrincipalName]]) {
        [issues addObject:@"UID 510 must map uniquely to _decisionos_codex."];
    }
    if (![bindings[@"gid_510_record_names"] isEqual:@[F01PrincipalName]]) {
        [issues addObject:@"GID 510 must map uniquely to _decisionos_codex."];
    }

    NSDictionary *held = snapshot[@"held_principals"];
    for (NSString *key in @[@"guardian_user", @"guardian_group",
                             @"broker_user", @"broker_group"]) {
        if (![held[key] isEqual:@[]]) {
            [issues addObject:[NSString stringWithFormat:
                @"Held principal %@ must be absent.", key]];
        }
    }
    NSDictionary *paths = snapshot[@"host_state_paths_present"];
    for (NSString *path in F01HostStatePaths()) {
        if (![paths[path] isEqual:@(NO)]) {
            [issues addObject:[NSString stringWithFormat:
                @"Host-state path must be absent: %@", path]];
        }
    }
    return issues;
}

typedef BOOL (^F01MutationOperation)(NSError **error);

static __attribute__((unused)) BOOL F01RequestDeletion(F01MutationOperation operation,
                                                       NSError **error) {
    (void)operation;
    if (error != NULL) {
        *error = F01Error(40,
                          @"Deletion is structurally disabled in this read-only artifact.",
                          @{
                              @"privileged_execution_authorized":
                                  @(PRIVILEGED_EXECUTION_AUTHORIZED),
                          });
    }
    return NO;
}

static NSDictionary *F01FailureReport(NSError *error) {
    return @{
        @"error": F01ErrorEvidence(error),
        @"mutation_attempted": @(NO),
        @"privileged_execution_authorized": @(PRIVILEGED_EXECUTION_AUTHORIZED),
        @"schema": F01Schema,
        @"status": @"HOLD_FRAMEWORK_READ_ERROR",
    };
}

static __attribute__((unused)) NSDictionary *F01QualificationReport(NSDictionary *snapshot) {
    NSArray *issues = F01ValidateSnapshot(snapshot);
    return @{
        @"issues": issues,
        @"mutation_attempted": @(NO),
        @"privileged_execution_authorized": @(PRIVILEGED_EXECUTION_AUTHORIZED),
        @"schema": F01Schema,
        @"snapshot": snapshot,
        @"status": issues.count == 0
            ? @"PASS_CURRENT_HOST_STATE_MATCH"
            : @"HOLD_CURRENT_HOST_STATE_MISMATCH",
    };
}

#if defined(F01_TESTING)

static NSData *F01FixturePolicyData(NSDictionary *policy) {
    return [NSPropertyListSerialization dataWithPropertyList:policy
                                                      format:NSPropertyListXMLFormat_v1_0
                                                     options:0
                                                       error:NULL];
}

static NSMutableDictionary *F01AcceptedFixture(void) {
    NSDictionary *userAttributes = @{
        kODAttributeTypeRecordName: @[F01PrincipalName],
        kODAttributeTypeUniqueID: @[F01NumericID],
        kODAttributeTypeGUID: @[F01UserGUID],
        kODAttributeTypePrimaryGroupID: @[F01NumericID],
        kODAttributeTypeFullName: @[F01RealName],
        kODAttributeTypeNFSHomeDirectory: @[F01Home],
        kODAttributeTypeRecordType: @[kODRecordTypeUsers],
        kODAttributeTypeMetaNodeLocation: @[F01NodeName],
        kODAttributeTypePassword: @[@"********"],
        F01NativeAccountPolicyData:
            @[@{ @"data_base64": [F01FixturePolicyData(@{ @"creationTime": @1 })
                                    base64EncodedStringWithOptions:0] }],
        F01NativeRecordDaemonVersion: @[@"fixture"],
    };
    NSDictionary *groupAttributes = @{
        kODAttributeTypeRecordName: @[F01PrincipalName],
        kODAttributeTypePrimaryGroupID: @[F01NumericID],
        kODAttributeTypeGUID: @[F01GroupGUID],
        kODAttributeTypeFullName: @[F01RealName],
        kODAttributeTypeRecordType: @[kODRecordTypeGroups],
        kODAttributeTypeMetaNodeLocation: @[F01NodeName],
        kODAttributeTypePassword: @[@"*"],
        F01NativeRecordDaemonVersion: @[@"fixture"],
    };
    return [@{
        @"execution": @{
            @"effective_uid": @501,
            @"mutation_attempted": @(NO),
            @"privileged_execution_authorized": @(NO),
        },
        @"held_principals": @{
            @"broker_group": @[],
            @"broker_user": @[],
            @"guardian_group": @[],
            @"guardian_user": @[],
        },
        @"host_state_paths_present": @{
            F01HostStatePaths()[0]: @(NO),
            F01HostStatePaths()[1]: @(NO),
            F01HostStatePaths()[2]: @(NO),
        },
        @"node": @{
            @"requested": F01NodeName,
            @"resolved": F01NodeName,
        },
        @"numeric_bindings": @{
            @"gid_510_record_names": @[F01PrincipalName],
            @"uid_510_record_names": @[F01PrincipalName],
        },
        @"records": @{
            @"group": @{
                @"attributes": groupAttributes,
                @"framework_record_name": F01PrincipalName,
                @"framework_record_type": kODRecordTypeGroups,
                @"match_count": @1,
                @"normalization_errors": @[],
            },
            @"user": @{
                @"attributes": userAttributes,
                @"framework_record_name": F01PrincipalName,
                @"framework_record_type": kODRecordTypeUsers,
                @"match_count": @1,
                @"normalization_errors": @[],
            },
        },
    } mutableCopy];
}

static NSMutableDictionary *F01DeepMutableCopy(NSDictionary *source) {
    NSData *data = [NSPropertyListSerialization dataWithPropertyList:source
                                                              format:NSPropertyListBinaryFormat_v1_0
                                                             options:0
                                                               error:NULL];
    return [NSPropertyListSerialization propertyListWithData:data
                                                     options:NSPropertyListMutableContainersAndLeaves
                                                      format:NULL
                                                       error:NULL];
}

static NSMutableDictionary *F01FixtureRecord(NSMutableDictionary *fixture,
                                             NSString *kind) {
    return fixture[@"records"][kind];
}

static NSMutableDictionary *F01FixtureAttributes(NSMutableDictionary *fixture,
                                                 NSString *kind) {
    return F01FixtureRecord(fixture, kind)[@"attributes"];
}

typedef void (^F01FixtureMutation)(NSMutableDictionary *fixture);

static void F01RecordTest(NSMutableArray *results,
                          NSString *name,
                          BOOL passed,
                          NSString *detail) {
    [results addObject:@{
        @"detail": detail ?: @"",
        @"name": name,
        @"passed": @(passed),
    }];
}

static void F01ExpectValidation(NSMutableArray *results,
                                NSString *name,
                                BOOL expectedPass,
                                F01FixtureMutation mutation) {
    NSMutableDictionary *fixture = F01DeepMutableCopy(F01AcceptedFixture());
    if (mutation != nil) {
        mutation(fixture);
    }
    NSArray *issues = F01ValidateSnapshot(fixture);
    BOOL actualPass = issues.count == 0;
    F01RecordTest(results,
                  name,
                  actualPass == expectedPass,
                  [issues componentsJoinedByString:@" | "]);
}

static NSDictionary *F01RunSelfTests(void) {
    NSMutableArray *results = [NSMutableArray array];
    NSMutableArray<NSString *> *normalizationErrors = [NSMutableArray array];
    NSDictionary *normalized = F01NormalizeAttributes(
        @{ @"fixture": @[@"z", @"a", @"m"] }, normalizationErrors);
    F01RecordTest(results,
                  @"multivalue_attributes_are_canonicalized",
                  [normalized[@"fixture"] isEqual:@[@"a", @"m", @"z"]] &&
                      normalizationErrors.count == 0,
                  @"");
    F01ExpectValidation(results, @"accepted_current_state", YES, nil);
    F01ExpectValidation(results, @"wrong_user_guid", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeGUID] = @[@"WRONG"];
    });
    F01ExpectValidation(results, @"wrong_group_guid", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypeGUID] = @[@"WRONG"];
    });
    F01ExpectValidation(results, @"wrong_uid", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeUniqueID] = @[@"511"];
    });
    F01ExpectValidation(results, @"wrong_user_gid", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypePrimaryGroupID] = @[@"511"];
    });
    F01ExpectValidation(results, @"wrong_group_gid", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypePrimaryGroupID] = @[@"511"];
    });
    F01ExpectValidation(results, @"wrong_user_real_name", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeFullName] = @[@"Wrong"];
    });
    F01ExpectValidation(results, @"wrong_group_real_name", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypeFullName] = @[@"Wrong"];
    });
    F01ExpectValidation(results, @"missing_nfs_home", NO, ^(NSMutableDictionary *f) {
        [F01FixtureAttributes(f, @"user") removeObjectForKey:kODAttributeTypeNFSHomeDirectory];
    });
    F01ExpectValidation(results, @"changed_nfs_home", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeNFSHomeDirectory] = @[@"/changed"];
    });
    F01ExpectValidation(results, @"user_shell_appears", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeUserShell] = @[@"/usr/bin/false"];
    });
    F01ExpectValidation(results, @"is_hidden_appears", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[F01NativeIsHidden] = @[@"1"];
    });
    F01ExpectValidation(results, @"authentication_authority_appears", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeAuthenticationAuthority] = @[@";DisabledUser;"];
    });
    F01ExpectValidation(results, @"group_membership_appears", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypeGroupMembership] = @[F01PrincipalName];
    });
    F01ExpectValidation(results, @"group_members_appears", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypeGroupMembers] = @[F01UserGUID];
    });
    F01ExpectValidation(results, @"guardian_user_exists", NO, ^(NSMutableDictionary *f) {
        f[@"held_principals"][@"guardian_user"] = @[F01GuardianName];
    });
    F01ExpectValidation(results, @"guardian_group_exists", NO, ^(NSMutableDictionary *f) {
        f[@"held_principals"][@"guardian_group"] = @[F01GuardianName];
    });
    F01ExpectValidation(results, @"broker_user_exists", NO, ^(NSMutableDictionary *f) {
        f[@"held_principals"][@"broker_user"] = @[F01BrokerName];
    });
    F01ExpectValidation(results, @"broker_group_exists", NO, ^(NSMutableDictionary *f) {
        f[@"held_principals"][@"broker_group"] = @[F01BrokerName];
    });
    F01ExpectValidation(results, @"duplicate_user_record", NO, ^(NSMutableDictionary *f) {
        F01FixtureRecord(f, @"user")[@"match_count"] = @2;
    });
    F01ExpectValidation(results, @"duplicate_group_record", NO, ^(NSMutableDictionary *f) {
        F01FixtureRecord(f, @"group")[@"match_count"] = @2;
    });
    F01ExpectValidation(results, @"ambiguous_uid_binding", NO, ^(NSMutableDictionary *f) {
        f[@"numeric_bindings"][@"uid_510_record_names"] = @[F01PrincipalName, @"other"];
    });
    F01ExpectValidation(results, @"ambiguous_gid_binding", NO, ^(NSMutableDictionary *f) {
        f[@"numeric_bindings"][@"gid_510_record_names"] = @[F01PrincipalName, @"other"];
    });
    F01ExpectValidation(results, @"wrong_opendirectory_node", NO, ^(NSMutableDictionary *f) {
        f[@"node"][@"resolved"] = @"/Search";
    });
    F01ExpectValidation(results, @"wrong_framework_record_name", NO, ^(NSMutableDictionary *f) {
        F01FixtureRecord(f, @"user")[@"framework_record_name"] = @"other";
    });
    F01ExpectValidation(results, @"unreviewed_user_attribute", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[@"dsAttrTypeNative:unexpected"] = @[@"value"];
    });
    F01ExpectValidation(results, @"unreviewed_group_attribute", NO, ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[@"dsAttrTypeNative:unexpected"] = @[@"value"];
    });
    F01ExpectValidation(results, @"unreviewed_account_policy", NO, ^(NSMutableDictionary *f) {
        NSData *policy = F01FixturePolicyData(@{ @"creationTime": @1,
                                                 @"passwordHistoryDepth": @1 });
        F01FixtureAttributes(f, @"user")[F01NativeAccountPolicyData] =
            @[@{ @"data_base64": [policy base64EncodedStringWithOptions:0] }];
    });
    F01ExpectValidation(results, @"host_state_tree_exists", NO, ^(NSMutableDictionary *f) {
        f[@"host_state_paths_present"][F01HostStatePaths()[0]] = @(YES);
    });

    NSError *frameworkError = [NSError errorWithDomain:@"com.apple.OpenDirectory"
                                                   code:777
                                               userInfo:@{
                                                   NSLocalizedDescriptionKey: @"fixture read failed",
                                                   @"detail": @"retained",
                                               }];
    NSDictionary *failure = F01FailureReport(frameworkError);
    BOOL retained = [failure[@"status"] isEqual:@"HOLD_FRAMEWORK_READ_ERROR"] &&
        [failure[@"error"][@"domain"] isEqual:@"com.apple.OpenDirectory"] &&
        [failure[@"error"][@"code"] isEqual:@777] &&
        [failure[@"error"][@"user_info"][@"detail"] isEqual:@"retained"];
    F01RecordTest(results, @"framework_read_error_retained", retained, @"");

    __block NSUInteger mutationCalls = 0;
    NSError *deletionError = nil;
    BOOL deletionResult = F01RequestDeletion(^BOOL(NSError **error) {
        mutationCalls += 1;
        if (error != NULL) {
            *error = nil;
        }
        return YES;
    }, &deletionError);
    BOOL deletionDisabled = !deletionResult && mutationCalls == 0 &&
        deletionError != nil &&
        [deletionError.domain isEqual:F01ErrorDomain] &&
        deletionError.code == 40;
    F01RecordTest(results, @"deletion_disabled_zero_mutation_calls",
                  deletionDisabled, @"");

    NSUInteger passed = 0;
    for (NSDictionary *result in results) {
        if ([result[@"passed"] boolValue]) {
            passed += 1;
        }
    }
    return @{
        @"failed": @(results.count - passed),
        @"passed": @(passed),
        @"schema": F01SelfTestSchema,
        @"tests": results,
        @"total": @(results.count),
    };
}

#endif

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        (void)argv;
        if (argc != 1) {
            NSDictionary *report = @{
                @"error": @"This artifact accepts no CLI arguments or runtime configuration.",
                @"mutation_attempted": @(NO),
                @"privileged_execution_authorized": @(PRIVILEGED_EXECUTION_AUTHORIZED),
                @"schema": F01Schema,
                @"status": @"HOLD_RUNTIME_INPUT_REJECTED",
            };
            F01WriteJSON(report);
            return 64;
        }
#if defined(F01_TESTING)
        NSDictionary *report = F01RunSelfTests();
        F01WriteJSON(report);
        return [report[@"failed"] unsignedIntegerValue] == 0 ? 0 : 1;
#else
        NSError *error = nil;
        NSDictionary *snapshot = F01ObserveHost(&error);
        NSDictionary *report = snapshot == nil
            ? F01FailureReport(error ?: F01Error(50, @"Unknown observation failure.", @{}))
            : F01QualificationReport(snapshot);
        F01WriteJSON(report);
        return [report[@"status"] isEqual:@"PASS_CURRENT_HOST_STATE_MATCH"] ? 0 : 2;
#endif
    }
}
