#import <Foundation/Foundation.h>
#import <OpenDirectory/OpenDirectory.h>

#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>

static NSString *const F01Schema = @"decision-os-f01-slice4a-opendirectory-mutation-v0.1";
static NSString *const F01SelfTestSchema = @"decision-os-f01-slice4a-opendirectory-mutation-self-test-v0.1";
static NSString *const F01ErrorDomain = @"DecisionOS.F01.OpenDirectoryMutation";
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
static const uid_t F01RequiredMutationEUID = 0;
static const NSUInteger F01PrivilegedInteractionBudget = 1;

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

static NSString *F01CanonicalSortKey(id value) {
    NSData *json = [NSJSONSerialization dataWithJSONObject:value
                                                   options:(NSJSONWritingSortedKeys |
                                                            NSJSONWritingFragmentsAllowed)
                                                     error:NULL];
    if (json == nil) {
        return [value description];
    }
    NSString *key = [[NSString alloc] initWithData:json encoding:NSUTF8StringEncoding];
    return key ?: [value description];
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
            return [F01CanonicalSortKey(left) compare:F01CanonicalSortKey(right)
                                              options:NSLiteralSearch];
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
                                     ODRecord **boundRecord,
                                     NSError **error) {
    if (boundRecord != NULL) {
        *boundRecord = nil;
    }
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
        ODRecord *record = candidate;
        NSDictionary *observation = F01RecordObservation(record, error);
        if (observation == nil) {
            return nil;
        }
        [result addEntriesFromDictionary:observation];
        if (boundRecord != NULL) {
            *boundRecord = record;
        }
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

@protocol F01MutationBackend <NSObject>
- (NSDictionary *)observe:(NSError **)error;
- (NSDictionary *)rebindExactCurrentRecords:(NSError **)error;
- (BOOL)deleteBoundUser:(NSError **)error;
- (BOOL)deleteBoundGroup:(NSError **)error;
@end

@interface F01OpenDirectoryBackend : NSObject <F01MutationBackend>
@property(nonatomic, strong) ODNode *node;
@property(nonatomic, strong) ODRecord *boundUser;
@property(nonatomic, strong) ODRecord *boundGroup;
- (instancetype)initWithError:(NSError **)error;
@end

@implementation F01OpenDirectoryBackend

- (instancetype)initWithError:(NSError **)error {
    self = [super init];
    if (self != nil) {
        _node = [ODNode nodeWithSession:[ODSession defaultSession]
                                   name:F01NodeName
                                  error:error];
        if (_node == nil) {
            return nil;
        }
    }
    return self;
}

- (NSDictionary *)observe:(NSError **)error {
    self.boundUser = nil;
    self.boundGroup = nil;

    ODRecord *userRecord = nil;
    NSDictionary *user = F01TargetRecord(self.node,
                                         kODRecordTypeUsers,
                                         &userRecord,
                                         error);
    if (user == nil) {
        return nil;
    }
    ODRecord *groupRecord = nil;
    NSDictionary *group = F01TargetRecord(self.node,
                                          kODRecordTypeGroups,
                                          &groupRecord,
                                          error);
    if (group == nil) {
        return nil;
    }

    NSArray *uidNames = F01RecordNames(self.node,
                                       kODRecordTypeUsers,
                                       kODAttributeTypeUniqueID,
                                       F01NumericID,
                                       error);
    if (uidNames == nil) {
        return nil;
    }
    NSArray *gidNames = F01RecordNames(self.node,
                                       kODRecordTypeGroups,
                                       kODAttributeTypePrimaryGroupID,
                                       F01NumericID,
                                       error);
    if (gidNames == nil) {
        return nil;
    }

    NSMutableDictionary *held = [NSMutableDictionary dictionary];
    for (NSString *recordType in @[kODRecordTypeUsers, kODRecordTypeGroups]) {
        NSString *kind = [recordType isEqualToString:kODRecordTypeUsers]
            ? @"user"
            : @"group";
        for (NSString *name in @[F01GuardianName, F01BrokerName]) {
            NSArray *matches = F01RecordNames(self.node,
                                              recordType,
                                              kODAttributeTypeRecordName,
                                              name,
                                              error);
            if (matches == nil) {
                return nil;
            }
            NSString *principal = [name isEqualToString:F01GuardianName]
                ? @"guardian"
                : @"broker";
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

    self.boundUser = userRecord;
    self.boundGroup = groupRecord;
    return @{
        @"held_principals": held,
        @"host_state_paths_present": paths,
        @"node": @{
            @"requested": F01NodeName,
            @"resolved": self.node.nodeName ?: [NSNull null],
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

- (NSDictionary *)rebindExactCurrentRecords:(NSError **)error {
    NSDictionary *baseline = [self observe:error];
    if (baseline == nil) {
        return nil;
    }

    ODRecord *userRecord = nil;
    NSDictionary *user = F01TargetRecord(self.node,
                                         kODRecordTypeUsers,
                                         &userRecord,
                                         error);
    if (user == nil) {
        return nil;
    }
    ODRecord *groupRecord = nil;
    NSDictionary *group = F01TargetRecord(self.node,
                                          kODRecordTypeGroups,
                                          &groupRecord,
                                          error);
    if (group == nil) {
        return nil;
    }

    NSMutableDictionary *records = [baseline[@"records"] mutableCopy];
    records[@"user"] = user;
    records[@"group"] = group;
    NSMutableDictionary *snapshot = [baseline mutableCopy];
    snapshot[@"records"] = records;
    self.boundUser = userRecord;
    self.boundGroup = groupRecord;
    return snapshot;
}

- (BOOL)deleteBoundUser:(NSError **)error {
    ODRecord *record = self.boundUser;
    if (record == nil) {
        if (error != NULL) {
            *error = F01Error(30, @"No exactly bound user record is available.", @{});
        }
        return NO;
    }
    BOOL deleted = [record deleteRecordAndReturnError:error];
    if (deleted) {
        self.boundUser = nil;
    }
    return deleted;
}

- (BOOL)deleteBoundGroup:(NSError **)error {
    ODRecord *record = self.boundGroup;
    if (record == nil) {
        if (error != NULL) {
            *error = F01Error(31, @"No exactly bound group record is available.", @{});
        }
        return NO;
    }
    BOOL deleted = [record deleteRecordAndReturnError:error];
    if (deleted) {
        self.boundGroup = nil;
    }
    return deleted;
}

@end

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
            @"%@ exposes unreviewed attributes: %@.",
            label, [ordered componentsJoinedByString:@", "]]];
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
    id plist = data == nil
        ? nil
        : [NSPropertyListSerialization propertyListWithData:data
                                                     options:0
                                                      format:NULL
                                                       error:&error];
    if (![plist isKindOfClass:[NSDictionary class]]) {
        [issues addObject:[NSString stringWithFormat:
            @"User accountPolicyData is not a dictionary plist%@.",
            error == nil
                ? @""
                : [NSString stringWithFormat:@" (%@/%ld)",
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

static NSSet<NSString *> *F01AllowedUserAttributes(void) {
    return [NSSet setWithArray:@[
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
}

static NSSet<NSString *> *F01AllowedGroupAttributes(void) {
    return [NSSet setWithArray:@[
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
}

static void F01ValidateNodeAndHeldSurfaces(NSMutableArray<NSString *> *issues,
                                           NSDictionary *snapshot) {
    NSDictionary *node = snapshot[@"node"];
    if (![node[@"requested"] isEqual:F01NodeName] ||
        ![node[@"resolved"] isEqual:F01NodeName]) {
        [issues addObject:@"OpenDirectory node must be exactly /Local/Default."];
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
}

static void F01ValidateExactUser(NSMutableArray<NSString *> *issues,
                                 NSDictionary *user) {
    if (![user[@"match_count"] isEqual:@1]) {
        [issues addObject:@"User record name must resolve uniquely."];
    }
    if (![user[@"normalization_errors"] isEqual:@[]]) {
        [issues addObject:@"User record normalization failed."];
    }
    if (![user[@"framework_record_name"] isEqual:F01PrincipalName] ||
        ![user[@"framework_record_type"] isEqual:kODRecordTypeUsers]) {
        [issues addObject:@"Framework user record identity mismatch."];
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
    F01RequireExactAttributeSurface(issues, user, F01AllowedUserAttributes(), @"User");
    F01RequireValues(issues, user, kODAttributeTypeRecordType,
                     @[kODRecordTypeUsers], @"User framework RecordType");
    F01RequireValues(issues, user, kODAttributeTypeMetaNodeLocation,
                     @[F01NodeName], @"User framework node location");
    F01RequireValues(issues, user, kODAttributeTypePassword,
                     @[@"********"], @"User non-credential password marker");
    F01RequireSafeAccountPolicy(issues, user);
}

static void F01ValidateExactGroup(NSMutableArray<NSString *> *issues,
                                  NSDictionary *group) {
    if (![group[@"match_count"] isEqual:@1]) {
        [issues addObject:@"Group record name must resolve uniquely."];
    }
    if (![group[@"normalization_errors"] isEqual:@[]]) {
        [issues addObject:@"Group record normalization failed."];
    }
    if (![group[@"framework_record_name"] isEqual:F01PrincipalName] ||
        ![group[@"framework_record_type"] isEqual:kODRecordTypeGroups]) {
        [issues addObject:@"Framework group record identity mismatch."];
    }
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
    F01RequireExactAttributeSurface(issues, group, F01AllowedGroupAttributes(), @"Group");
    F01RequireValues(issues, group, kODAttributeTypeRecordType,
                     @[kODRecordTypeGroups], @"Group framework RecordType");
    F01RequireValues(issues, group, kODAttributeTypeMetaNodeLocation,
                     @[F01NodeName], @"Group framework node location");
    F01RequireValues(issues, group, kODAttributeTypePassword,
                     @[@"*"], @"Group non-credential password marker");
}

static void F01ValidateAbsentRecord(NSMutableArray<NSString *> *issues,
                                    NSDictionary *record,
                                    NSString *label) {
    if (![record[@"match_count"] isEqual:@0] ||
        ![record[@"attributes"] isEqual:@{}] ||
        record[@"framework_record_name"] != [NSNull null] ||
        record[@"framework_record_type"] != [NSNull null] ||
        ![record[@"normalization_errors"] isEqual:@[]]) {
        [issues addObject:[NSString stringWithFormat:
            @"%@ must be absent with no bound framework record.", label]];
    }
}

static NSArray<NSString *> *F01ValidateCurrentSnapshot(NSDictionary *snapshot) {
    NSMutableArray<NSString *> *issues = [NSMutableArray array];
    F01ValidateNodeAndHeldSurfaces(issues, snapshot);
    NSDictionary *records = snapshot[@"records"];
    F01ValidateExactUser(issues, records[@"user"]);
    F01ValidateExactGroup(issues, records[@"group"]);
    NSDictionary *bindings = snapshot[@"numeric_bindings"];
    if (![bindings[@"uid_510_record_names"] isEqual:@[F01PrincipalName]]) {
        [issues addObject:@"UID 510 must map uniquely to _decisionos_codex."];
    }
    if (![bindings[@"gid_510_record_names"] isEqual:@[F01PrincipalName]]) {
        [issues addObject:@"GID 510 must map uniquely to _decisionos_codex."];
    }
    return issues;
}

static NSArray<NSString *> *F01ValidateAfterUserDeletion(NSDictionary *snapshot) {
    NSMutableArray<NSString *> *issues = [NSMutableArray array];
    F01ValidateNodeAndHeldSurfaces(issues, snapshot);
    NSDictionary *records = snapshot[@"records"];
    F01ValidateAbsentRecord(issues, records[@"user"], @"User record");
    F01ValidateExactGroup(issues, records[@"group"]);
    NSDictionary *bindings = snapshot[@"numeric_bindings"];
    if (![bindings[@"uid_510_record_names"] isEqual:@[]]) {
        [issues addObject:@"UID 510 must be free after user deletion."];
    }
    if (![bindings[@"gid_510_record_names"] isEqual:@[F01PrincipalName]]) {
        [issues addObject:@"GID 510 must remain uniquely bound before group deletion."];
    }
    return issues;
}

static NSArray<NSString *> *F01ValidateFinalSnapshot(NSDictionary *snapshot) {
    NSMutableArray<NSString *> *issues = [NSMutableArray array];
    F01ValidateNodeAndHeldSurfaces(issues, snapshot);
    NSDictionary *records = snapshot[@"records"];
    F01ValidateAbsentRecord(issues, records[@"user"], @"User record");
    F01ValidateAbsentRecord(issues, records[@"group"], @"Group record");
    NSDictionary *bindings = snapshot[@"numeric_bindings"];
    if (![bindings[@"uid_510_record_names"] isEqual:@[]]) {
        [issues addObject:@"UID 510 must be free after rollback."];
    }
    if (![bindings[@"gid_510_record_names"] isEqual:@[]]) {
        [issues addObject:@"GID 510 must be free after rollback."];
    }
    return issues;
}

static NSMutableDictionary *F01BaseReport(NSString *status,
                                          NSArray<NSString *> *completed,
                                          BOOL mutationAttempted,
                                          uid_t effectiveUID) {
    return [@{
        @"authorization_retry_allowed": @(NO),
        @"completed_mutations": completed,
        @"effective_uid": @(effectiveUID),
        @"gate": @"HOLD",
        @"mutation_attempted": @(mutationAttempted),
        @"privileged_execution_authorized":
            @((BOOL)(effectiveUID == F01RequiredMutationEUID)),
        @"privileged_interaction_budget": @(F01PrivilegedInteractionBudget),
        @"privileged_prompt_count": @0,
        @"protected_repository_acl_changed": @(NO),
        @"provisioning_performed": @(NO),
        @"schema": F01Schema,
        @"status": status,
    } mutableCopy];
}

static NSDictionary *F01IssueReport(NSString *status,
                                    NSArray<NSString *> *issues,
                                    NSDictionary *snapshot,
                                    NSArray<NSString *> *completed,
                                    BOOL mutationAttempted,
                                    uid_t effectiveUID,
                                    NSString *phase) {
    NSMutableDictionary *report = F01BaseReport(status,
                                                completed,
                                                mutationAttempted,
                                                effectiveUID);
    report[@"issues"] = issues;
    report[@"phase"] = phase;
    report[@"snapshot"] = snapshot;
    return report;
}

static NSDictionary *F01NSErrorReport(NSString *status,
                                      NSError *error,
                                      NSArray<NSString *> *completed,
                                      BOOL mutationAttempted,
                                      uid_t effectiveUID,
                                      NSString *phase) {
    NSMutableDictionary *report = F01BaseReport(status,
                                                completed,
                                                mutationAttempted,
                                                effectiveUID);
    report[@"error"] = F01ErrorEvidence(error);
    report[@"phase"] = phase;
    return report;
}

static NSDictionary *F01ObserveOrError(id<F01MutationBackend> backend,
                                       NSError **error) {
    NSError *observationError = nil;
    NSDictionary *snapshot = [backend observe:&observationError];
    if (snapshot == nil && error != NULL) {
        *error = observationError ?: F01Error(40, @"Unknown OpenDirectory observation failure.", @{});
    }
    return snapshot;
}

static NSDictionary *F01RebindOrError(id<F01MutationBackend> backend,
                                      NSError **error) {
    NSError *observationError = nil;
    NSDictionary *snapshot = [backend rebindExactCurrentRecords:&observationError];
    if (snapshot == nil && error != NULL) {
        *error = observationError ?: F01Error(43, @"Unknown OpenDirectory rebind failure.", @{});
    }
    return snapshot;
}

static NSDictionary *F01ExecuteForEUID(id<F01MutationBackend> backend,
                                       uid_t effectiveUID) {
    NSMutableArray<NSString *> *completed = [NSMutableArray array];
    NSError *error = nil;
    NSDictionary *snapshot = F01ObserveOrError(backend, &error);
    if (snapshot == nil) {
        return F01NSErrorReport(@"HOLD_FRAMEWORK_READ_ERROR",
                                error,
                                completed,
                                NO,
                                effectiveUID,
                                @"initial_observation");
    }
    NSArray *issues = F01ValidateCurrentSnapshot(snapshot);
    if (issues.count != 0) {
        return F01IssueReport(@"HOLD_CURRENT_HOST_STATE_MISMATCH",
                              issues,
                              snapshot,
                              completed,
                              NO,
                              effectiveUID,
                              @"initial_observation");
    }
    if (effectiveUID != F01RequiredMutationEUID) {
        return F01IssueReport(@"HOLD_PRIVILEGE_REQUIRED",
                              @[],
                              snapshot,
                              completed,
                              NO,
                              effectiveUID,
                              @"unprivileged_read_qualification");
    }

    snapshot = F01RebindOrError(backend, &error);
    if (snapshot == nil) {
        return F01NSErrorReport(@"HOLD_FRAMEWORK_READ_ERROR",
                                error,
                                completed,
                                NO,
                                effectiveUID,
                                @"immediate_pre_user_delete_rebind");
    }
    issues = F01ValidateCurrentSnapshot(snapshot);
    if (issues.count != 0) {
        return F01IssueReport(@"HOLD_PRE_USER_DELETE_REBIND_FAILED",
                              issues,
                              snapshot,
                              completed,
                              NO,
                              effectiveUID,
                              @"immediate_pre_user_delete_rebind");
    }

    error = nil;
    if (![backend deleteBoundUser:&error]) {
        return F01NSErrorReport(@"HOLD_USER_DELETE_FAILED",
                                error ?: F01Error(41, @"User deletion failed without NSError.", @{}),
                                completed,
                                YES,
                                effectiveUID,
                                @"user_delete");
    }
    [completed addObject:@"user_deleted"];

    snapshot = F01ObserveOrError(backend, &error);
    if (snapshot == nil) {
        return F01NSErrorReport(@"HOLD_FRAMEWORK_READ_ERROR",
                                error,
                                completed,
                                YES,
                                effectiveUID,
                                @"post_user_delete_verification");
    }
    issues = F01ValidateAfterUserDeletion(snapshot);
    if (issues.count != 0) {
        return F01IssueReport(@"HOLD_POST_USER_DELETE_VERIFICATION_FAILED",
                              issues,
                              snapshot,
                              completed,
                              YES,
                              effectiveUID,
                              @"post_user_delete_verification");
    }

    snapshot = F01ObserveOrError(backend, &error);
    if (snapshot == nil) {
        return F01NSErrorReport(@"HOLD_FRAMEWORK_READ_ERROR",
                                error,
                                completed,
                                YES,
                                effectiveUID,
                                @"immediate_pre_group_delete_rebind");
    }
    issues = F01ValidateAfterUserDeletion(snapshot);
    if (issues.count != 0) {
        return F01IssueReport(@"HOLD_PRE_GROUP_DELETE_REBIND_FAILED",
                              issues,
                              snapshot,
                              completed,
                              YES,
                              effectiveUID,
                              @"immediate_pre_group_delete_rebind");
    }

    error = nil;
    if (![backend deleteBoundGroup:&error]) {
        return F01NSErrorReport(@"HOLD_GROUP_DELETE_FAILED",
                                error ?: F01Error(42, @"Group deletion failed without NSError.", @{}),
                                completed,
                                YES,
                                effectiveUID,
                                @"group_delete");
    }
    [completed addObject:@"group_deleted"];

    snapshot = F01ObserveOrError(backend, &error);
    if (snapshot == nil) {
        return F01NSErrorReport(@"HOLD_FRAMEWORK_READ_ERROR",
                                error,
                                completed,
                                YES,
                                effectiveUID,
                                @"final_verification");
    }
    issues = F01ValidateFinalSnapshot(snapshot);
    if (issues.count != 0) {
        return F01IssueReport(@"HOLD_FINAL_VERIFICATION_FAILED",
                              issues,
                              snapshot,
                              completed,
                              YES,
                              effectiveUID,
                              @"final_verification");
    }

    NSMutableDictionary *report = F01BaseReport(
        @"ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW",
        completed,
        YES,
        effectiveUID);
    report[@"gid_510_free"] = @(YES);
    report[@"passed"] = @(YES);
    report[@"phase"] = @"complete";
    report[@"snapshot"] = snapshot;
    report[@"uid_510_free"] = @(YES);
    return report;
}

#if defined(F01_TESTING)

static NSData *F01FixturePolicyData(NSDictionary *policy) {
    return [NSPropertyListSerialization dataWithPropertyList:policy
                                                      format:NSPropertyListXMLFormat_v1_0
                                                     options:0
                                                       error:NULL];
}

static NSDictionary *F01AbsentRecord(void) {
    return @{
        @"attributes": @{},
        @"framework_record_name": [NSNull null],
        @"framework_record_type": [NSNull null],
        @"match_count": @0,
        @"normalization_errors": @[],
    };
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
    NSData *data = [NSJSONSerialization dataWithJSONObject:source
                                                   options:0
                                                     error:NULL];
    return [NSJSONSerialization JSONObjectWithData:data
                                           options:NSJSONReadingMutableContainers
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

typedef void (^F01FixtureDrift)(NSMutableDictionary *state);

@interface F01FixtureBackend : NSObject <F01MutationBackend>
@property(nonatomic, strong) NSMutableDictionary *state;
@property(nonatomic, strong) NSMutableArray<NSString *> *deleteCalls;
@property(nonatomic, strong) NSMutableArray<NSString *> *events;
@property(nonatomic) NSUInteger observationCount;
@property(nonatomic) NSUInteger rebindCount;
@property(nonatomic) NSUInteger observationErrorAt;
@property(nonatomic) NSUInteger driftObservation;
@property(nonatomic, copy) F01FixtureDrift drift;
@property(nonatomic, copy) F01FixtureDrift rebindDrift;
@property(nonatomic, strong) NSError *observationError;
@property(nonatomic, strong) NSError *userDeleteError;
@property(nonatomic, strong) NSError *groupDeleteError;
@property(nonatomic) BOOL retainUIDAfterUserDelete;
@property(nonatomic) BOOL retainGIDAfterGroupDelete;
@property(nonatomic) BOOL driftGroupAfterUserDelete;
@end

@implementation F01FixtureBackend

- (instancetype)init {
    self = [super init];
    if (self != nil) {
        _state = F01DeepMutableCopy(F01AcceptedFixture());
        _deleteCalls = [NSMutableArray array];
        _events = [NSMutableArray array];
    }
    return self;
}

- (NSDictionary *)observe:(NSError **)error {
    [self.events addObject:@"observe"];
    self.observationCount += 1;
    if (self.observationErrorAt == self.observationCount) {
        if (error != NULL) {
            *error = self.observationError ?: F01Error(70, @"Fixture observation failed.", @{});
        }
        return nil;
    }
    if (self.driftObservation == self.observationCount && self.drift != nil) {
        self.drift(self.state);
    }
    return F01DeepMutableCopy(self.state);
}

- (NSDictionary *)rebindExactCurrentRecords:(NSError **)error {
    (void)error;
    [self.events addObject:@"rebind_both"];
    self.rebindCount += 1;
    if (self.rebindDrift != nil) {
        self.rebindDrift(self.state);
    }
    return F01DeepMutableCopy(self.state);
}

- (BOOL)deleteBoundUser:(NSError **)error {
    [self.events addObject:@"delete_user"];
    [self.deleteCalls addObject:@"user"];
    if (self.userDeleteError != nil) {
        if (error != NULL) {
            *error = self.userDeleteError;
        }
        return NO;
    }
    self.state[@"records"][@"user"] = F01AbsentRecord();
    if (!self.retainUIDAfterUserDelete) {
        self.state[@"numeric_bindings"][@"uid_510_record_names"] = @[];
    }
    if (self.driftGroupAfterUserDelete) {
        F01FixtureAttributes(self.state, @"group")[kODAttributeTypeGUID] = @[@"WRONG"];
    }
    return YES;
}

- (BOOL)deleteBoundGroup:(NSError **)error {
    [self.events addObject:@"delete_group"];
    [self.deleteCalls addObject:@"group"];
    if (self.groupDeleteError != nil) {
        if (error != NULL) {
            *error = self.groupDeleteError;
        }
        return NO;
    }
    self.state[@"records"][@"group"] = F01AbsentRecord();
    if (!self.retainGIDAfterGroupDelete) {
        self.state[@"numeric_bindings"][@"gid_510_record_names"] = @[];
    }
    return YES;
}

@end

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

static void F01ExpectZeroDelete(NSMutableArray *results,
                                NSString *name,
                                F01FixtureDrift mutation) {
    F01FixtureBackend *backend = [[F01FixtureBackend alloc] init];
    mutation(backend.state);
    NSDictionary *report = F01ExecuteForEUID(backend, 0);
    BOOL passed = backend.deleteCalls.count == 0 &&
        [report[@"completed_mutations"] isEqual:@[]] &&
        [report[@"mutation_attempted"] isEqual:@(NO)];
    F01RecordTest(results, name, passed, report[@"status"]);
}

static NSDictionary *F01RunSelfTests(void) {
    NSMutableArray *results = [NSMutableArray array];

    F01ExpectZeroDelete(results, @"wrong_user_guid_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeGUID] = @[@"WRONG"];
    });
    F01ExpectZeroDelete(results, @"wrong_group_guid_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypeGUID] = @[@"WRONG"];
    });
    F01ExpectZeroDelete(results, @"wrong_uid_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeUniqueID] = @[@"511"];
    });
    F01ExpectZeroDelete(results, @"wrong_user_gid_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypePrimaryGroupID] = @[@"511"];
    });
    F01ExpectZeroDelete(results, @"wrong_group_gid_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypePrimaryGroupID] = @[@"511"];
    });
    F01ExpectZeroDelete(results, @"wrong_user_real_name_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeFullName] = @[@"Wrong"];
    });
    F01ExpectZeroDelete(results, @"wrong_group_real_name_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypeFullName] = @[@"Wrong"];
    });
    F01ExpectZeroDelete(results, @"missing_nfs_home_zero_deletes", ^(NSMutableDictionary *f) {
        [F01FixtureAttributes(f, @"user") removeObjectForKey:kODAttributeTypeNFSHomeDirectory];
    });
    F01ExpectZeroDelete(results, @"changed_nfs_home_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeNFSHomeDirectory] = @[@"/changed"];
    });
    F01ExpectZeroDelete(results, @"user_shell_appears_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeUserShell] = @[@"/usr/bin/false"];
    });
    F01ExpectZeroDelete(results, @"is_hidden_appears_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[F01NativeIsHidden] = @[@"1"];
    });
    F01ExpectZeroDelete(results, @"authentication_authority_appears_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeAuthenticationAuthority] = @[@";DisabledUser;"];
    });
    F01ExpectZeroDelete(results, @"group_membership_appears_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypeGroupMembership] = @[F01PrincipalName];
    });
    F01ExpectZeroDelete(results, @"group_members_appears_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"group")[kODAttributeTypeGroupMembers] = @[F01UserGUID];
    });
    F01ExpectZeroDelete(results, @"guardian_appears_zero_deletes", ^(NSMutableDictionary *f) {
        f[@"held_principals"][@"guardian_user"] = @[F01GuardianName];
    });
    F01ExpectZeroDelete(results, @"broker_appears_zero_deletes", ^(NSMutableDictionary *f) {
        f[@"held_principals"][@"broker_group"] = @[F01BrokerName];
    });
    F01ExpectZeroDelete(results, @"host_state_path_appears_zero_deletes", ^(NSMutableDictionary *f) {
        f[@"host_state_paths_present"][F01HostStatePaths()[0]] = @(YES);
    });
    F01ExpectZeroDelete(results, @"duplicate_user_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureRecord(f, @"user")[@"match_count"] = @2;
    });
    F01ExpectZeroDelete(results, @"duplicate_group_zero_deletes", ^(NSMutableDictionary *f) {
        F01FixtureRecord(f, @"group")[@"match_count"] = @2;
    });
    F01ExpectZeroDelete(results, @"ambiguous_uid_zero_deletes", ^(NSMutableDictionary *f) {
        f[@"numeric_bindings"][@"uid_510_record_names"] = @[F01PrincipalName, @"other"];
    });
    F01ExpectZeroDelete(results, @"ambiguous_gid_zero_deletes", ^(NSMutableDictionary *f) {
        f[@"numeric_bindings"][@"gid_510_record_names"] = @[F01PrincipalName, @"other"];
    });
    F01ExpectZeroDelete(results, @"wrong_node_zero_deletes", ^(NSMutableDictionary *f) {
        f[@"node"][@"resolved"] = @"/Search";
    });

    F01FixtureBackend *rebindDrift = [[F01FixtureBackend alloc] init];
    rebindDrift.rebindDrift = ^(NSMutableDictionary *f) {
        F01FixtureAttributes(f, @"user")[kODAttributeTypeGUID] = @[@"WRONG"];
    };
    NSDictionary *rebindReport = F01ExecuteForEUID(rebindDrift, 0);
    F01RecordTest(results,
                  @"immediate_rebind_drift_zero_deletes",
                  rebindDrift.deleteCalls.count == 0 &&
                      [rebindReport[@"status"] isEqual:@"HOLD_PRE_USER_DELETE_REBIND_FAILED"],
                  rebindReport[@"status"]);

    NSError *userError = [NSError errorWithDomain:@"com.apple.OpenDirectory"
                                              code:777
                                          userInfo:@{
                                              NSLocalizedDescriptionKey: @"fixture user delete failed",
                                              @"detail": @"retained",
                                          }];
    F01FixtureBackend *userFailure = [[F01FixtureBackend alloc] init];
    userFailure.userDeleteError = userError;
    NSDictionary *userFailureReport = F01ExecuteForEUID(userFailure, 0);
    BOOL userFailurePassed = [userFailure.deleteCalls isEqual:@[@"user"]] &&
        [userFailureReport[@"completed_mutations"] isEqual:@[]] &&
        [userFailureReport[@"status"] isEqual:@"HOLD_USER_DELETE_FAILED"] &&
        [userFailureReport[@"error"][@"domain"] isEqual:@"com.apple.OpenDirectory"] &&
        [userFailureReport[@"error"][@"code"] isEqual:@777] &&
        [userFailureReport[@"error"][@"user_info"][@"detail"] isEqual:@"retained"];
    F01RecordTest(results,
                  @"accepted_state_reaches_user_delete_and_retains_nserror",
                  userFailurePassed,
                  userFailureReport[@"status"]);

    F01FixtureBackend *uidNotFree = [[F01FixtureBackend alloc] init];
    uidNotFree.retainUIDAfterUserDelete = YES;
    NSDictionary *uidReport = F01ExecuteForEUID(uidNotFree, 0);
    F01RecordTest(results,
                  @"uid_not_free_blocks_group_delete",
                  [uidNotFree.deleteCalls isEqual:@[@"user"]] &&
                      [uidReport[@"completed_mutations"] isEqual:@[@"user_deleted"]] &&
                      [uidReport[@"status"] isEqual:@"HOLD_POST_USER_DELETE_VERIFICATION_FAILED"],
                  uidReport[@"status"]);

    F01FixtureBackend *groupDrift = [[F01FixtureBackend alloc] init];
    groupDrift.driftGroupAfterUserDelete = YES;
    NSDictionary *groupDriftReport = F01ExecuteForEUID(groupDrift, 0);
    F01RecordTest(results,
                  @"group_change_after_user_delete_blocks_group_delete",
                  [groupDrift.deleteCalls isEqual:@[@"user"]] &&
                      [groupDriftReport[@"completed_mutations"] isEqual:@[@"user_deleted"]],
                  groupDriftReport[@"status"]);

    NSError *groupError = [NSError errorWithDomain:@"com.apple.OpenDirectory"
                                               code:778
                                           userInfo:@{NSLocalizedDescriptionKey:
                                                          @"fixture group delete failed"}];
    F01FixtureBackend *groupFailure = [[F01FixtureBackend alloc] init];
    groupFailure.groupDeleteError = groupError;
    NSDictionary *groupFailureReport = F01ExecuteForEUID(groupFailure, 0);
    F01RecordTest(results,
                  @"group_delete_error_has_no_retry",
                  [groupFailure.deleteCalls isEqual:@[@"user", @"group"]] &&
                      [groupFailureReport[@"completed_mutations"] isEqual:@[@"user_deleted"]] &&
                      [groupFailureReport[@"status"] isEqual:@"HOLD_GROUP_DELETE_FAILED"] &&
                      [groupFailureReport[@"error"][@"code"] isEqual:@778],
                  groupFailureReport[@"status"]);

    F01FixtureBackend *gidNotFree = [[F01FixtureBackend alloc] init];
    gidNotFree.retainGIDAfterGroupDelete = YES;
    NSDictionary *gidReport = F01ExecuteForEUID(gidNotFree, 0);
    F01RecordTest(results,
                  @"gid_not_free_fails_final_verification_without_retry",
                  [gidNotFree.deleteCalls isEqual:@[@"user", @"group"]] &&
                      [gidReport[@"completed_mutations"] isEqual:@[@"user_deleted", @"group_deleted"]] &&
                      [gidReport[@"status"] isEqual:@"HOLD_FINAL_VERIFICATION_FAILED"],
                  gidReport[@"status"]);

    F01FixtureBackend *frameworkFailure = [[F01FixtureBackend alloc] init];
    frameworkFailure.observationErrorAt = 1;
    frameworkFailure.observationError = [NSError errorWithDomain:@"com.apple.OpenDirectory"
                                                             code:779
                                                         userInfo:@{
                                                             NSLocalizedDescriptionKey: @"fixture read failed",
                                                             @"detail": @"native",
                                                         }];
    NSDictionary *frameworkReport = F01ExecuteForEUID(frameworkFailure, 0);
    F01RecordTest(results,
                  @"framework_read_error_retained_zero_deletes",
                  frameworkFailure.deleteCalls.count == 0 &&
                      [frameworkReport[@"error"][@"domain"] isEqual:@"com.apple.OpenDirectory"] &&
                      [frameworkReport[@"error"][@"code"] isEqual:@779] &&
                      [frameworkReport[@"error"][@"user_info"][@"detail"] isEqual:@"native"],
                  frameworkReport[@"status"]);

    F01FixtureBackend *unprivileged = [[F01FixtureBackend alloc] init];
    NSDictionary *unprivilegedReport = F01ExecuteForEUID(unprivileged, 501);
    F01RecordTest(results,
                  @"unprivileged_exact_state_has_zero_mutation_calls",
                  unprivileged.observationCount == 1 &&
                      unprivileged.deleteCalls.count == 0 &&
                      [unprivilegedReport[@"status"] isEqual:@"HOLD_PRIVILEGE_REQUIRED"] &&
                      [unprivilegedReport[@"mutation_attempted"] isEqual:@(NO)] &&
                      CFGetTypeID((__bridge CFTypeRef)
                          unprivilegedReport[@"privileged_execution_authorized"]) ==
                          CFBooleanGetTypeID() &&
                      ![unprivilegedReport[@"privileged_execution_authorized"] boolValue] &&
                      [unprivilegedReport[@"completed_mutations"] isEqual:@[]],
                  unprivilegedReport[@"status"]);

    F01FixtureBackend *success = [[F01FixtureBackend alloc] init];
    NSDictionary *successReport = F01ExecuteForEUID(success, 0);
    F01RecordTest(results,
                  @"successful_transaction_two_deletes_in_order",
                  [success.deleteCalls isEqual:@[@"user", @"group"]] &&
                      [success.events isEqual:@[
                          @"observe",
                          @"rebind_both",
                          @"delete_user",
                          @"observe",
                          @"observe",
                          @"delete_group",
                          @"observe",
                      ]] &&
                      success.observationCount == 4 &&
                      success.rebindCount == 1 &&
                      [successReport[@"completed_mutations"]
                          isEqual:@[@"user_deleted", @"group_deleted"]] &&
                      [successReport[@"status"]
                          isEqual:@"ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW"] &&
                      [successReport[@"uid_510_free"] isEqual:@(YES)] &&
                      [successReport[@"gid_510_free"] isEqual:@(YES)],
                  successReport[@"status"]);

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
                @"authorization_retry_allowed": @(NO),
                @"completed_mutations": @[],
                @"error": @"This artifact accepts no CLI arguments or runtime configuration.",
                @"mutation_attempted": @(NO),
                @"privileged_prompt_count": @0,
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
        uid_t effectiveUID = geteuid();
        NSError *error = nil;
        F01OpenDirectoryBackend *backend =
            [[F01OpenDirectoryBackend alloc] initWithError:&error];
        NSDictionary *report = backend == nil
            ? F01NSErrorReport(@"HOLD_FRAMEWORK_READ_ERROR",
                                error ?: F01Error(50, @"Cannot open /Local/Default.", @{}),
                                @[],
                                NO,
                                effectiveUID,
                                @"open_local_default")
            : F01ExecuteForEUID(backend, effectiveUID);
        F01WriteJSON(report);
        NSString *status = report[@"status"];
        if ([status isEqual:@"ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW"]) {
            return 0;
        }
        if ([status isEqual:@"HOLD_PRIVILEGE_REQUIRED"]) {
            return 3;
        }
        return 2;
#endif
    }
}
